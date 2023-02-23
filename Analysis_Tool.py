from flet import *
import pandas as pd
import fastf1
import fastf1.plotting
from datetime import datetime
import numpy as np
import requests
import math

BG = '#041955'
FWG = '#97b4ff'
FG = '#3450a1'
PINK = '#eb06ff'
fastf1.Cache.enable_cache('cache')


def GetNextEvent():
    races = []
    previous_result = {
        'pos': [],
        'driver': []
    }

    schedule = fastf1.get_events_remaining(datetime.today())
    previous_event_name = ""
    df = pd.DataFrame(schedule)
    url = "http://ergast.com/api/f1/{}/last/results.json"

    if pd.to_datetime(df[0:1]['Session3Date'].values[0]) >= datetime.today():
        link = url.format(datetime.today().year-1)

        headers = {}
        try:
            response = requests.request("GET", url=link, headers=headers)
            data = response.json()

            previous_event_name = data["MRData"]['RaceTable']['Races'][0]['raceName']

            for i in data["MRData"]['RaceTable']['Races']:
                for driver in i['Results']:
                    previous_result['pos'].append(driver['position'])
                    previous_result['driver'].append(
                        f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}")
        except:
            pass

    else:
        link = url.format(datetime.today().year)
        try:
            response = requests.request("GET", url=link, headers=headers)
            data = response.json()

            previous_event_name = data["MRData"]['RaceTable']['Races'][0]['raceName']

            for i in data["MRData"]['RaceTable']['Races']:
                for driver in i['Results']:
                    previous_result['pos'].append(driver['position'])
                    previous_result['driver'].append(
                        f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}")
        except:
            pass

    print(link)

    for i in df["EventName"]:
        races.append(i)

    return races, previous_result, previous_event_name


races_remaining, previous, pre_event = GetNextEvent()


def main(page: Page):

    page.title = 'F1 Analysis Tool'
    page.fonts = {
        'quick': 'Quicksand-VariableFont_wght.ttf'
    }

    def open_menu(e):
        main_screen.controls[0].expand = False
        main_screen.controls[0].width = 100
        page.update()

    def close_menu(e):
        main_screen.controls[0].expand = True
        page.update()

    def ToggleQuali(e):
        races_dropdown.value = None
        races_strategy_dropdown.value = None
        races_dropdown.options = None
        races_strategy_dropdown.options = None
        years_dropdown.value = None
        quali_lv.controls.clear()
        strategy_lv.controls.clear()

        main_screen.controls[0].content = None
        main_screen.controls[0].content = quali_prediction
        main_screen.controls[0].expand = True
        page.update()

    def ToggleHome(e):
        main_screen.controls[0].content = None
        main_screen.controls[0].content = main_contents
        main_screen.controls[0].expand = True

        races_dropdown.value = None
        races_strategy_dropdown.value = None
        races_dropdown.options = None
        races_strategy_dropdown.options = None
        years_dropdown.value = None
        quali_lv.controls.clear()
        strategy_lv.controls.clear()
        page.update()

    def ToggleTelemetry(e):
        races_dropdown.value = None
        races_strategy_dropdown.value = None
        years_dropdown.value = None
        quali_lv.controls.clear()

    def ToggleStrategy(e):
        races_dropdown.value = None
        races_strategy_dropdown.value = None
        races_dropdown.options = None
        races_strategy_dropdown.options = None
        years_dropdown.value = None
        quali_lv.controls.clear()
        strategy_lv.controls.clear()

        main_screen.controls[0].content = None
        main_screen.controls[0].content = strategy_prediction
        main_screen.controls[0].expand = True
        page.update()

    def OnDetermine(e):
        loading_container.controls.append(ProgressRing(
            color=BG, tooltip='Running algorithm...May take a while...'))
        page.update()

        prac1, prac2, prac3 = GetPracticeData(
            int(years_dropdown.value), races_strategy_dropdown.value)

        combined_df = pd.concat([prac1, prac2, prac3],
                                axis=0, ignore_index=True)

        combined_df = combined_df[combined_df['IsAccurate'] == True]
        teams = list(set(combined_df['Team']))
        compounds = list(set(combined_df['Compound']))

        compounds_speed_dictionary = {}
        for team in teams:
            team_df = combined_df[combined_df['Team'] == team]
            compounds_speed_dictionary[team] = []
            for comp in compounds:
                avg = combined_df[combined_df['Compound']
                                  == comp]['TyreLife'].mean()
                mx = combined_df[combined_df['Compound']
                                 == comp]['TyreLife'].max()

                max_laps = math.ceil(avg+mx)

                compound_df = team_df[team_df['Compound'] == comp]

                avg_lap_time = compound_df['LapTime'].mean()

                compounds_speed_dictionary[team].append(
                    {'compound': comp, 'pace': avg_lap_time, 'life': max_laps})

        fastest_strat = {}
        for key, value in compounds_speed_dictionary.items():
            fastest_strat[key] = []
            values = sorted(value, key=lambda k: k['pace'])
            compounds_speed_dictionary[key] = values

        for key, value in compounds_speed_dictionary.items():
            fastest_strat[key].append(value[0]['compound'])
            fastest_strat[key].append(value[1]['compound'])

        for key, value in fastest_strat.items():
            strategy_lv.controls.append(
                Row(
                    controls=[
                        Container(
                            expand=True,
                            content=Text(
                                f"{key}", text_align='center', font_family='quick')
                        ),
                        Container(
                            expand=True,
                            content=Text(
                                f"{value[0]} to {value[1]}", text_align='center', font_family='quick')
                        ),
                    ]
                )
            )

        loading_container.controls.clear()
        page.update()

    def GetPracticeData(year, gp):
        try:
            practice1 = fastf1.get_session(year, gp, 'Practice 1')
            practice1.load(laps=True)
            prac1 = pd.DataFrame(practice1.laps)
        except:
            prac1 = pd.DataFrame()

        try:
            practice2 = fastf1.get_session(year, gp, 'Practice 2')
            practice2.load(laps=True)
            prac2 = pd.DataFrame(practice2.laps)
        except:
            prac2 = pd.DataFrame()

        try:
            practice3 = fastf1.get_session(year, gp, 'Practice 3')
            practice3.load(laps=True)
            prac3 = pd.DataFrame(practice3.laps)
        except:
            prac3 = pd.DataFrame()

        return prac1, prac2, prac3

    def OnGrandPrixChange(e):
        loading_container.controls.append(ProgressRing(
            color=BG, tooltip='Running algorithm...May take a while...'))
        page.update()

        prac1, prac2, prac3 = GetPracticeData(
            int(years_dropdown.value), races_dropdown.value)
        quali_predictions = {}
        combined_df = pd.concat([prac1, prac2, prac3],
                                axis=0, ignore_index=True)
        combined_df = combined_df[combined_df['IsAccurate'] == True]
        drivers = list(set(combined_df['Driver'].values))

        for driver in drivers:
            temp = combined_df[combined_df['Driver'] == driver]
            s1Times = []
            s2Times = []
            s3Times = []

            for i in temp.index:
                s1Times.append(temp['Sector1Time'][i])
                s2Times.append(temp['Sector2Time'][i])
                s3Times.append(temp['Sector3Time'][i])

            s1Times.sort()
            s2Times.sort()
            s3Times.sort()

            if len(s1Times) > 0 and len(s2Times) > 0 and len(s3Times) > 0:
                laptime = s1Times[0] + s2Times[0] + s3Times[0]
                quali_predictions[driver] = laptime
            else:
                pass

        quali_predictions = pd.Series(
            quali_predictions).sort_values().to_dict()

        count = 0
        for key, val in quali_predictions.items():
            count += 1

            x = str(val).split(":")
            final = f"{x[1][-1:]}:{x[2][:-3]}"

            pos_container = Container(expand=True,
                                      content=Text(f"{count}.\t{key}\t{final}", text_align='center',
                                                   ), bgcolor='#343a40', border=border.only(left=border.BorderSide(1, "white"), bottom=border.BorderSide(1, "white")))

            if count % 2 == 0:
                quali_lv.controls.append(
                    Row(
                        controls=[
                            Container(
                                expand=True,
                            ),
                            Container(
                                expand=True,
                                content=pos_container
                            ),
                        ]
                    )
                )
            else:
                quali_lv.controls.append(
                    Row(
                        controls=[
                            Container(
                                expand=True,
                                content=pos_container
                            ),
                            Container(
                                expand=True,
                            ),
                        ]
                    )
                )

        loading_container.controls.clear()
        page.update()

    def OnYearChange(e):
        races = []

        schedule = fastf1.get_event_schedule(int(e.control.value))
        df = pd.DataFrame(schedule)

        for i in df.index:
            if df['EventFormat'][i] != 'testing':
                races.append(dropdown.Option(df['EventName'][i]))

        races_dropdown.options = races
        races_strategy_dropdown.options = races

        page.update()

    years = []
    for i in reversed(range(2003, datetime.today().year+1)):
        years.append(dropdown.Option(i))

    races_dropdown = Dropdown(
        label='Grand Prix', alignment=alignment.center, options=None, bgcolor=FWG, border_radius=20, color='white', border_color=FG, content_padding=5, label_style=TextStyle(color='white'), on_change=lambda e: OnGrandPrixChange(e))
    years_dropdown = Dropdown(label='Year', alignment=alignment.center,
                              options=years, bgcolor=FWG, border_radius=20, color='white', border_color=FG, content_padding=5, label_style=TextStyle(color='white'), on_change=lambda e: OnYearChange(e))
    races_strategy_dropdown = Dropdown(
        label='Grand Prix', alignment=alignment.center, options=None, bgcolor=FWG, border_radius=20, color='white', border_color=FG, content_padding=5, label_style=TextStyle(color='white'), on_change=lambda e: OnDetermine(e))

    quali_lv = ListView(
        expand=True,
        spacing=5,
        padding=10,
        divider_thickness=0,
    )

    strategy_lv = ListView(
        expand=True,
        spacing=5,
        padding=10,
        divider_thickness=1,
    )

    loading_container = Row(height=20, alignment='center')

    quali_prediction = Container(
        clip_behavior=ClipBehavior.HARD_EDGE,
        content=Column(
            controls=[
                Row(  # Icon Nav Strip
                    alignment='spaceBetween',
                    controls=[
                        Container(content=Icon(icons.MENU),
                                  on_click=lambda e: open_menu(e)),
                        Row(
                            controls=[
                                Container(content=Icon(icons.SEARCH)),
                                Container(content=Icon(
                                    icons.NOTIFICATIONS_OUTLINED))
                            ]
                        )
                    ],
                ),
                Container(height=20),
                Text('Qualifying Predictions', size=25,
                     color='WHITE', font_family='quick'),
                Text(
                    'Select a Year and a Race', size=15, color=FWG, font_family='quick'),
                Container(height=30),
                Container(
                    expand=True,
                    content=Row(
                        alignment='spaceEvenly',
                        controls=[
                            Container(
                                clip_behavior=ClipBehavior.HARD_EDGE,
                                expand=True,
                                bgcolor=FWG,
                                content=Column(
                                    expand=True,
                                    controls=[
                                        Row(
                                            alignment='spaceEvenly',
                                            controls=[
                                                Container(
                                                    expand=True, content=years_dropdown, padding=10),
                                                Container(
                                                    expand=True, content=races_dropdown, padding=10),
                                            ]
                                        ),
                                        loading_container,
                                        Container(
                                            clip_behavior=ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER,
                                            expand=True,
                                            content=quali_lv
                                        )
                                    ]
                                ),
                                padding=padding.only(
                                    top=5, left=5,
                                    bottom=5, right=5,
                                ),
                                margin=5,
                                border_radius=15
                            ),
                        ]
                    ),
                    padding=padding.only(
                        top=5, left=5,
                        bottom=5, right=5,
                    )
                )
            ]
        )
    )

    strategy_prediction = Container(
        clip_behavior=ClipBehavior.HARD_EDGE,
        content=Column(
            controls=[
                Row(  # Icon Nav Strip
                    alignment='spaceBetween',
                    controls=[
                        Container(content=Icon(icons.MENU),
                                  on_click=lambda e: open_menu(e)),
                        Row(
                            controls=[
                                Container(content=Icon(icons.SEARCH)),
                                Container(content=Icon(
                                    icons.NOTIFICATIONS_OUTLINED))
                            ]
                        )
                    ],
                ),
                Container(height=20),
                Text('Strategy Predictions', size=25,
                     color='WHITE', font_family='quick'),
                Text(
                    'Select a Year and a Race', size=15, color=FWG, font_family='quick'),
                Container(height=30),
                Container(
                    expand=True,
                    content=Row(
                        alignment='spaceEvenly',
                        controls=[
                            Container(
                                clip_behavior=ClipBehavior.HARD_EDGE,
                                expand=True,
                                bgcolor=FWG,
                                content=Column(
                                    expand=True,
                                    controls=[
                                        Row(
                                            alignment='spaceEvenly',
                                            controls=[
                                                Container(
                                                    expand=True, content=years_dropdown, padding=10),
                                                Container(
                                                    expand=True, content=races_strategy_dropdown, padding=10),
                                            ]
                                        ),
                                        loading_container,
                                        Container(
                                            clip_behavior=ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER,
                                            expand=True,
                                            content=strategy_lv
                                        )
                                    ]
                                ),
                                padding=padding.only(
                                    top=5, left=5,
                                    bottom=5, right=5,
                                ),
                                margin=5,
                                border_radius=15
                            ),
                        ]
                    ),
                    padding=padding.only(
                        top=5, left=5,
                        bottom=5, right=5,
                    )
                )
            ]
        )
    )

    lv = ListView(
        expand=True,
        spacing=5,
        padding=20,
        divider_thickness=1,
    )

    df = pd.DataFrame(previous)
    for i in df.index:
        lv.controls.append(
            Row(
                controls=[
                    Container(
                        expand=True,
                        content=Text(
                            df['pos'][i], size=11, color='white', font_family='quick', text_align='center')
                    ),
                    Container(
                        expand=True,
                        content=Text(
                            df['driver'][i], size=11, color='white', font_family='quick', text_align='center')
                    ),
                ]
            )
        )

    main_contents = Container(
        clip_behavior=ClipBehavior.HARD_EDGE,
        content=Column(
            controls=[
                Row(  # Icon Nav Strip
                    alignment='spaceBetween',
                    controls=[
                        Container(content=Icon(icons.MENU),
                                  on_click=lambda e: open_menu(e)),
                        Row(
                            controls=[
                                Container(content=Icon(
                                    icons.NOTIFICATIONS_OUTLINED))
                            ]
                        )
                    ],
                ),
                Container(height=20),
                Text('Formula 1 - Analysis App', size=25,
                     color='WHITE', font_family='quick'),
                Text(
                    f'Next Race - {races_remaining[0]}', size=15, color=FWG, font_family='quick'),
                Container(height=30),
                Container(
                    expand=True,
                    content=Row(
                        alignment='spaceEvenly',
                        controls=[
                            Container(
                                clip_behavior=ClipBehavior.HARD_EDGE,
                                expand=True,
                                bgcolor=FWG,
                                content=Column(
                                    alignment=MainAxisAlignment.CENTER,
                                    expand=True,
                                    controls=[
                                        Text(f'Previous Race Result - {pre_event}', size=15,
                                             color=BG, font_family='quick'),

                                        Row(
                                            alignment='spaceEvenly',
                                            controls=[
                                                Text(
                                                    'Position', size=15, color=BG, font_family='quick'),
                                                Text(
                                                    'Driver', size=15, color=BG, font_family='quick')
                                            ]
                                        ),

                                        Container(
                                            clip_behavior=ClipBehavior.ANTI_ALIAS_WITH_SAVE_LAYER,
                                            expand=True,
                                            content=lv
                                        )
                                    ]
                                ),
                                padding=padding.only(
                                    top=5, left=5,
                                    bottom=5, right=5,
                                ),
                                margin=5,
                                border_radius=15
                            ),
                        ]
                    ),
                    padding=padding.only(
                        top=5, left=5,
                        bottom=5, right=5,
                    )
                )
            ]
        )
    )

    menu_contents = Container(
        expand=True,
        content=Column(
            controls=[
                Row(  # Nav Strip
                    controls=[
                        Container(content=Icon(icons.CLOSE),
                                  on_click=lambda e: close_menu(e)),
                        Container(content=Text(
                            'Select an Option:', font_family='quick')),
                    ],
                ),
                Container(height=20),
                Column(  # Menu Buttons
                    alignment=MainAxisAlignment.CENTER,
                    controls=[
                        FilledButton(text="Home", icon=icons.HOME,
                                     on_click=lambda e: ToggleHome(e), width=150),
                        FilledButton(text="Telemetry",
                                     icon=icons.QUERY_STATS, width=150, on_click=lambda e: ToggleTelemetry(e)),
                        FilledButton(text="Strategy",
                                     icon=icons.APP_REGISTRATION, width=150, on_click=lambda e: ToggleStrategy(e)),
                        FilledButton(text="Qualifying", icon=icons.LEADERBOARD,
                                     on_click=lambda e: ToggleQuali(e), width=150),
                    ])
            ]
        )
    )

    menu = Row(
        alignment='start',
        expand=True,
        controls=[
            Container(
                border_radius=50,
                padding=padding.only(
                    top=50, left=20,
                    bottom=50, right=20,
                ),
                content=menu_contents
            )
        ]
    )
    main_screen = Row(
        alignment='end',
        controls=[
            Container(
                expand=True,
                bgcolor=FG,
                border_radius=50,
                animate=animation.Animation(1000, AnimationCurve.EASE),
                padding=padding.only(
                    top=50, left=20,
                    bottom=50, right=20,
                ),
                content=main_contents
            )
        ]
    )

    container = Container(
        clip_behavior=ClipBehavior.HARD_EDGE,
        expand=True,
        bgcolor=BG,
        border_radius=50,
        content=Stack(
            controls=[
                menu,
                main_screen,
            ]
        )
    )
    page.add(container)


app(target=main)
