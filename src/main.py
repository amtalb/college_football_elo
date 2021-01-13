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


def draw_header():
    st.title("College Football Elo Rankings")

    # option = st.selectbox("Season", ("2018", "2019", "2020"))


def draw_intro():
    st.write(
        """This is my attempt to bring Elo rankings to College Football. 
        I have never been a fan of how college football chooses its champions. 
        From the days of split national titles, to the BCS, and even the Playoff, 
        the whole process seems very opaque unfair to the 'have-nots' of the 
        college football world (i.e. everyone not in the SEC)"""
    )
    st.write(
        """With that being said, I figured why not try to come up with an earth-
        shattering solution that will fundamentally change college football rankings 
        forever all by myself? Once that didn't pan out, I ended up with this, 
        an attempt to apply Elo ratings to the college football world. Elo was a
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


def main():
    st.set_page_config(
        page_title="College Football Elo Rankings",
        page_icon="🏈",
        layout="centered",
        initial_sidebar_state="auto",
    )
    draw_header()

    reg_elo = False
    cum_elo = False
    mov_elo = False
    recruit_elo = False
    conf_elo = False

    reg_elo = st.sidebar.button("Elo")
    cum_elo = st.sidebar.button("Cumulative")
    mov_elo = st.sidebar.button("Margin of Victory")
    recruit_elo = st.sidebar.button("Recruiting")
    conf_elo = st.sidebar.button("Conferences")

    if reg_elo:
        st.table(get_ranking(elo.get_elo_rankings(season="2020")))
        expander = st.beta_expander("Methodology")
        expander.write(
            """The original Elo ranking system taken straight from Wikipedia. Each team in
            the contest has an expected outcome calculated as follows:"""
        )
        expander.latex(
            r"\frac{1}{1 + (10^{\frac{away \space elo - home \space elo}{400})}}"
        )
        expander.write(
            """The expected outcome is then compared to the actual outcome (1 for a win, 0
            for a loss) and multiplied by a constant $K$, which in this case is 50. The resulting
            value is the team's net Elo, which will be positive or negative based on whether
            they won or lost."""
        )
        expander.write("Data from https://www.collegefootballdata.com/")
    elif cum_elo:
        st.table(get_ranking(elo.get_elo_rankings(season="all")))
        expander = st.beta_expander("Methodology")
        expander.write(
            """This ranking system is almost exactly the same as the regular Elo ranking system
            except a team's Elo carries over, year over year. However, at the end of the season,
            a teams Elo is "reset" by regressing 70% of the way to the mean. This is to ensure that
            past successes aren't an excuse for a bad current season."""
        )
        expander.write("Data from https://www.collegefootballdata.com/exporter/")
    elif mov_elo:
        st.table(
            get_ranking(elo.get_elo_rankings(season="2020", margin_of_victory=True))
        )
        expander = st.beta_expander("Methodology")
        expander.write(
            """
            Elo's are adjusted based on the margin of victory of the game. When a team wins
            by blowout, they earn more points, on a diminishing scale. the margin of 
            victory is used to calculate a multiplier that affects the team's new Elo. The 
            multiplier formula is as follows:"""
        )
        expander.latex(
            r"\ln(margin \space of \space victory + 1) * \frac{2.2}{difference \space in \space elo * 0.001 + 2.2}"
        )
        expander.write(
            "Taken from 538: https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/"
        )
        expander.write("")
        expander.write("Data from https://www.collegefootballdata.com/")
    elif recruit_elo:
        st.table(get_ranking(elo.get_elo_rankings(season="2020", recruiting=True)))
        expander = st.beta_expander("Methodology")
        expander.write(
            """Each team's starting Elo is modified based on their average 24/7 Sports 
            recruiting score for the past 5 seasons. This average is then halved and added/subtracted
            from a base of 1500 to set starting Elo scores."""
        )
        expander.write("")
        expander.write("Data from https://www.collegefootballdata.com/")
    elif conf_elo:
        st.table(get_ranking(elo.get_elo_rankings(season="2020", conference=True)))
        expander = st.beta_expander("Methodology")
        expander.write(
            """Conference weights are completely mine and completely arbitrary. 
            I roughly based them on how teams did in the 2019/2020 bowl season. 
            See conference starting Elo's below  and, believe me, it hurt me just
            as much to add to the echo chamber of the SEC being the best:"""
        )
        expander.write(
            """
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
        )
        expander.write("")
        expander.write("Data from https://www.collegefootballdata.com/")
    else:
        draw_intro()


if __name__ == "__main__":
    main()
