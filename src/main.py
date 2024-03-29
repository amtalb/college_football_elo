from datetime import datetime

import streamlit as st

import elo


def get_ranking(df):
    try:
        df.sort_values(by=["Elo"], ascending=False, inplace=True)
    except:
        pass

    df.reset_index(drop=True, inplace=True)
    df.index += 1
    return df.head(25)


def set_page_config():
    st.set_page_config(
        page_title="College Football Elo Rankings",
        page_icon="🏈",
        layout="centered",
        initial_sidebar_state="auto",
    )


def draw_header():
    st.title("College Football Elo Rankings")


def draw_intro():
    st.write(
        """This is my attempt to bring Elo rankings to College Football. 
        I have never been a fan of how college football chooses its champions. 
        From the days of split national titles, to the BCS, and even the Playoff, 
        the whole process seems very opaque and unfair to the 'have-nots' of the 
        college football world (i.e. everyone not in the SEC)"""
    )
    st.write(
        """With that being said, I figured why not try to come up with an earth-
        shattering solution that will fundamentally change college football rankings 
        forever all by myself? Once that didn't pan out, I ended up with this, 
        an attempt to apply Elo ratings to the college football world. Mr. Elo was a
        very smart fellow who devised a rating system for chess players back in the
        day. His system (with slight modifications) is still in use today as the 
        primary way to compare chess players."""
    )
    st.write(
        """Elo rankings are very simple. Each player has an Elo score and when they 
        compete against each other, the winner takes some Elo points from the loser.
        The amount of points taken or lost depend on the relative difference in the player's
        starting Elo scores. The tougher an opponent is, the more points you will gain by 
        beating them, for example. If you'd like to learn more, look it up on Wikipedia, because
        I'm too lazy to link it here."""
    )
    st.write(
        """On the sidebar, I have concocted various Elo-based rating systems for the 2020 college
        football season (before bowls). The first one is the most true to a "normal" Elo system and the others 
        each have some slight modifications. The details for each model are in the "Methodology"
        section at the bottom of the page."""
    )
    st.write("https://github.com/amtalb/college_football_elo")


def get_true_key(dictionary):
    for key, value in dictionary.items():
        if value is True:
            return key
    return None


def get_last_ten_years_as_str() -> list[str]:
    return [str(x) for x in range(datetime.now().year - 10, datetime.now().year)]


def draw_page():
    if "sb_page" in st.session_state:
        match st.session_state["sb_page"]:
            case "reg":
                subheader = "Regular Elo Ratings"
                season_box = True
                margin_of_victory = False
                recruiting = False
                conference = False
                methodology_string = """
                    The original Elo ranking system taken straight from Wikipedia. Each team in
                    the contest has an expected outcome calculated as follows:\n
                    \t1 / (1 + 10 ^ ( (away_elo - home_elo) / 400 ))\n
                    The expected outcome is then compared to the actual outcome (1 for a win, 0
                    for a loss) and multiplied by a constant $K$, which in this case is 50. The resulting
                    value is the team's net Elo, which will be positive or negative based on whether
                    they won or lost.
                """
                data_from_string = "Data from https://www.collegefootballdata.com/"
            case "cum":
                subheader = "Cumulative Elo Ratings"
                season_box = False
                methodology_string = """
                    This ranking system is almost exactly the same as the regular Elo ranking system
                    except a team's Elo carries over, year over year. However, at the end of the season,
                    a teams Elo is "reset" by regressing 70% of the way to the mean. This is to ensure that
                    past successes aren't an excuse for a bad current season.
                """
                data_from_string = (
                    "Data from https://www.collegefootballdata.com/exporter/"
                )
            case "mov":
                subheader = "Margin-of-victory Elo Ratings"
                season_box = True
                margin_of_victory = True
                recruiting = False
                conference = False
                methodology_string = """
                    Elos are adjusted based on the margin of victory of the game. When a team wins
                    by blowout, they earn more points, on a diminishing scale. the margin of
                    victory is used to calculate a multiplier that affects the team's new Elo. The
                    multiplier formula is as follows:\n
                    \tln(margin_of_victory + 1) * 2.2 / (difference_in_elo * 0.001 + 2.2)\n
                    Taken from 538: https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/
                """
                data_from_string = "Data from https://www.collegefootballdata.com/"
            case "recruit":
                subheader = "Elo Ratings weighted by recruiting class rank"
                season_box = True
                margin_of_victory = False
                recruiting = True
                conference = False
                methodology_string = """
                    Each team's starting Elo is modified based on their average
                    recruiting score for the past 5 seasons. This average is then halved and added/subtracted
                    from a base of 1500 to set starting Elo scores.
                """
                data_from_string = "Data from https://www.collegefootballdata.com/"
            case "conf":
                subheader = "Conference-weighted Elo Ratings"
                season_box = True
                margin_of_victory = False
                recruiting = False
                conference = True
                methodology_string = """
                    Conference weights are completely mine and completely arbitrary.
                    I roughly based them on how teams did in the 2019/2020 bowl season.
                    See conference starting Elo's below  and, believe me, it hurt me just
                    as much to add to the echo chamber of the SEC being the best:
                        - ACC: 1510
                        - AAC: 1475
                        - Big 10: 1540
                        - Big 12: 1535
                        - Conference USA: 1460
                        - FBS Independents: 1500
                        - Mid American: 1450
                        - Mountain West: 1460
                        - Pac 12: 1510
                        - SEC: 1550
                        - Sun Belt: 1480
                """
                data_from_string = "Data from https://www.collegefootballdata.com/"

        st.subheader(subheader)

        if season_box:
            season = st.selectbox("Season", get_last_ten_years_as_str())

            with st.spinner("Crunching some numbers..."):
                st.table(
                    get_ranking(
                        elo.get_elo_rankings(
                            season=season,
                            margin_of_victory=margin_of_victory,
                            recruiting=recruiting,
                            conference=conference,
                        )
                    )
                )
        else:
            st.text(f"Seasons {datetime.now().year - 10}-{datetime.now().year - 1}")
            with st.spinner("Crunching some numbers..."):
                st.table(get_ranking(elo.get_elo_rankings(season="all")))

        expander = st.expander("Methodology")
        expander.write(methodology_string)
        expander.write("")
        expander.write(data_from_string)

    else:
        draw_intro()


def main():
    # set up page
    set_page_config()

    # add header
    draw_header()

    # add sidebar
    reg = st.sidebar.button("Elo")
    cum = st.sidebar.button("Cumulative")
    mov = st.sidebar.button("Margin of Victory")
    recruit = st.sidebar.button("Recruiting")
    conf = st.sidebar.button("Conferences")

    # update state to represent selected sidebar tab
    if reg:
        st.session_state["sb_page"] = "reg"
    elif cum:
        st.session_state["sb_page"] = "cum"
    elif mov:
        st.session_state["sb_page"] = "mov"
    elif recruit:
        st.session_state["sb_page"] = "recruit"
    elif conf:
        st.session_state["sb_page"] = "conf"

    if "sb_page" in st.session_state:
        print(st.session_state["sb_page"])

    # add the main page contents depending on sidebar state
    draw_page()


if __name__ == "__main__":
    main()
