import flet as ft
import requests
import pandas as pd

API_BASE = "https://api.openf1.org/v1"

def get_session_info():
    # Automatically finds the most recent session (detects test days & race weekends)
    try:
        response = requests.get(f"{API_BASE}/sessions?year=2026").json()
        latest = response[-1]
        return latest['session_key'], latest['location'], latest['session_name']
    except:
        return None, "Unknown", "No Session Found"

def main(page: ft.Page):
    page.title = "F1 Ultra-Telemetry"
    page.theme_mode = ft.ThemeMode.DARK
    session_key, location, session_name = get_session_info()

    # --- UI COMPONENTS ---
    title = ft.Text(f"📍 {location} | {session_name}", size=22, weight="bold", color="yellow")
    rankings_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    telemetry_chart = ft.LineChart(expand=True)
    
    # --- REPLAY & RANKING LOGIC ---
    def update_data(e=None):
        # 1. Update Rankings
        pos_res = requests.get(f"{API_BASE}/position?session_key={session_key}").json()
        df = pd.DataFrame(pos_res).sort_values('date').groupby('driver_number').last()
        df = df.sort_values('position')

        rankings_col.controls.clear()
        for d_num, row in df.iterrows():
            rankings_col.controls.append(
                ft.ListTile(
                    title=ft.Text(f"P{int(row['position'])} - Driver #{d_num}"),
                    on_click=lambda _, n=d_num: start_replay(n)
                )
            )
        page.update()

    def start_replay(driver_num):
        # 2. Replay Telemetry for any car
        data = requests.get(f"{API_BASE}/car_data?driver_number={driver_num}&session_key={session_key}").json()
        points = [ft.LineChartDataPoint(i, d['speed']) for i, d in enumerate(data[-50:])]
        
        telemetry_chart.data_series = [
            ft.LineChartData(data_points=points, color=ft.colors.CYAN, stroke_width=3)
        ]
        page.snack_bar = ft.SnackBar(ft.Text(f"Showing Replay for #{driver_num}"))
        page.snack_bar.open = True
        page.update()

    # --- TABS LAYOUT ---
    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        tabs=[
            ft.Tab(text="Rankings", icon=ft.icons.LEADERBOARD, content=rankings_col),
            ft.Tab(text="Telemetry Replay", icon=ft.icons.SPEED, content=telemetry_chart),
        ]
    )

    page.add(title, ft.IconButton(ft.icons.REFRESH, on_click=update_data), tabs)
    update_data()

ft.app(target=main)
