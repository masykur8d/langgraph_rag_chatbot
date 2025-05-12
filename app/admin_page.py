import os
import asyncio
from typing import Literal, Optional, List

from nicegui import ui, app, run, events, binding
from fastapi import Request
import pandas as pd

from fastapi.responses import RedirectResponse

from utils.python_utils import localeText
from components.user_db import get_table_data
from components.vector_db import get_vector_data, add_vector_data, get_specific_vector_data, remove_vector

import google_oauth
from google_oauth import is_authenticated, session_info

@ui.page('/admin', favicon='🚀', title='AIサポートデスク管理画面')
async def admin_page(request: Request):
    # ======================================== Checking session login status ========================================
    if not is_authenticated(request):
        return RedirectResponse('/login?next=/admin')
    session = session_info[request.session['id']]

    # -------------------------- Starting app loding -------------------------- #
    with ui.card().tight().classes('fixed-center') as startup_element:
        with ui.column().classes('fixed-center'):
            ui.spinner('comment', size='13em', color="deep-purple")
    
    await ui.context.client.connected(timeout=120)

    # -------------------------- Initialize database -------------------------- #
    shop_information = await run.io_bound(get_table_data, 'users')
    if shop_information.empty:
        return

    # -------------------------- Dialog section -------------------------- #
    with ui.dialog().props('persistent') as reset_dialog, ui.card():
        ui.markdown('管理画面を初めからやります？')
        with ui.row().classes('w-full'):
            ui.space()
            ui.button('適用', color='teal', on_click=lambda: ui.navigate.reload())
            ui.button('キャンセル', on_click=lambda: reset_dialog.close())

    with ui.dialog().props('maximized persistent transition-show="scale" transition-hide="scale"') as waiting_downloding_account, ui.card().classes("bg-transparent"):
        with ui.column(align_items='center').classes('absolute-center w-2/4'):
            ui.spinner('hourglass', size='15em', color="light-green").classes('items-center')
            with ui.linear_progress(value=0, size='25px', show_value=False, color='warning').props('stripe rounded') as downloading_account_progress:
                with ui.row(align_items='center').classes('absolute-center'):
                    progress_text_percentage = ui.badge(color='white', text_color='accent')
    
    def flash_screen(
            progress: Optional[float] = None, 
            progress_text: Optional[int] = None,
            status: Optional[Literal['open', 'close']] = None, 
        ):
        if status == 'open':
            waiting_downloding_account.open()
        elif status == 'close':
            waiting_downloding_account.close()
        
        if (
            progress is not None 
            and progress_text is not None
        ):
            downloading_account_progress.set_value(progress)
            progress_text_percentage.set_text(f'{progress_text}%')

    # -------------------------- Header section -------------------------- #
    with ui.header(bordered=True).classes('items-center text-black bg-white h-[5rem]'), ui.column(align_items='center').classes('w-full mx-auto'):
        with ui.row(align_items='center').classes('w-full no-wrap items-center'):
            with ui.avatar(color="white", rounded=True):
                ui.image(source='/icon/bot_icon.png')
                ui.badge(color='green').props('floating rounded').classes('animate-bounce')
            ui.markdown(f'AIサポートデスク<br>**管理画面**')
            ui.space()
            with ui.column(align_items='center'):
                ui.button(icon='restart_alt', on_click=lambda: reset_dialog.open()).props('flat size="lg" padding="xs md"')
    
    # -------------------------- Body section -------------------------- #
    with ui.stepper().props('horizontal flat header-nav animated keep-alive').classes('w-full no-wrap') as stepper:
        with ui.step('チャットアカウント', icon='settings'):
            with ui.column(align_items='center').classes('w-full mx-auto'):
                users_table_options = {
                    "defaultColDef": {
                        "editable": True,
                        "minWidth": 160,
                        "resizable": True,
                        "sortable": True,
                        "headerCheckboxSelection": False,
                        "headerCheckboxSelectionFilteredOnly": True,
                        "floatingFilter": True,
                        "headerClass": "font-bold",
                    },
                    "columnDefs": [
                        {
                            'headerName': 'ドメイン',
                            'field': 'shop_name_en',
                            "checkboxSelection": True,
                            "headerCheckboxSelection": True,
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': '店舗名',
                            'field': 'shop_name_jp',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': '商材',
                            'field': 'shop_product',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': '無効',
                            "editable": False,
                            'field': 'disabled',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': 'BOT名',
                            'field': 'bot_name',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            }
                        },
                        {
                            'headerName': 'Q&Aのデータベース',
                            'field': 'vector_db_namespace',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            }
                        },
                        {
                            'headerName': 'チャットプロンプト',
                            'field': 'openai_chat_prompt',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "cellEditor": "agLargeTextCellEditor",
                            "cellEditorPopup": True,
                            "cellEditorParams": {
                                "rows": 15,
                                "cols": 50
                            },
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            }
                        },
                        {
                            'headerName': 'スピーチプロンプト',
                            'field': 'openai_speech_prompt',
                            'filter': 'agNumberColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "cellEditor": "agLargeTextCellEditor",
                            "cellEditorPopup": True,
                            "cellEditorParams": {
                                "rows": 15,
                                "cols": 50
                            },
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': '最初のメッセージ',
                            'field': 'first_message',
                            'filter': 'agNumberColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "cellEditor": "agLargeTextCellEditor",
                            "cellEditorPopup": True,
                            "cellEditorParams": {
                                "rows": 15,
                                "cols": 50
                            },
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                    ],
                    "rowData": shop_information.to_dict('records'),
                    "suppressDragLeaveHidesColumns": True,
                    "rowModelType": "clientSide",
                    "rowSelection": "multiple",
                    "rowMultiSelectWithClick": True,
                    "suppressRowDeselection": False,
                    "suppressRowClickSelection": False,
                    "groupSelectsChildren": True,
                    "groupSelectsFiltered": True,
                    "animateRows": True,
                    "alwaysShowHorizontalScroll": True,
                    "localeText": localeText,
                }
                users_table = ui.aggrid(users_table_options, theme='material', auto_size_columns=True).classes('h-[calc(100vh-300px)]')
                # users_table.on('cellValueChanged', lambda event: print(event))

                class AllVectorData:
                    def __init__(self):
                        self.df_all_vector_data = pd.DataFrame()
                        self.df_selected_account = pd.DataFrame()
                        self.list_namespaces: Optional[List[str]] = None
                    
                    async def download_acocunts_vectors(self, table: ui.aggrid):
                        selected_accounts = await ui.run_javascript(f'getElement({table.id}).api.getSelectedNodes().map(node => node.data.id)')
                        selected_account_index = [item for item in selected_accounts]

                        if selected_account_index:
                            self.df_selected_account = shop_information[shop_information['id'].isin(selected_account_index)]
                            self.list_namespaces = self.df_selected_account['vector_db_namespace'].unique().tolist()
                            self.list_shop_name_en = self.df_selected_account['shop_name_en'].unique().tolist()

                            database_name_select.set_options(self.list_namespaces)
                            shop_name_en_select.set_options(self.list_shop_name_en)

                            flash_screen(progress=0, progress_text=0, status='open')

                            list_df_account_vector = []
                            for row_index, account in self.df_selected_account.iterrows():
                                shop_name_en = account['shop_name_en']
                                account_id = account['id']
                                namespace = account['vector_db_namespace']

                                vector_database = await run.io_bound(get_vector_data, namespace)
                                await asyncio.sleep(2.5)

                                vector_database['account_id'] = account_id
                                vector_database['shop_name_en'] = shop_name_en
                                vector_database['vector_db_namespace'] = namespace

                                list_df_account_vector.append(vector_database)

                                progress_value = float((row_index + 1) / len(self.df_selected_account.index))
                                flash_screen(progress=progress_value, progress_text=int(progress_value*100))

                            self.df_all_vector_data = pd.concat(list_df_account_vector)

                        vector_table.options.update(
                            {
                                "rowData": self.df_all_vector_data.to_dict('records'),
                            }
                        )
                        vector_table.update()
                        
                        await asyncio.sleep(2.5)
                        flash_screen(status='close')
                        stepper.next()

                all_vector_data = AllVectorData()

                with ui.row(align_items='center').classes('w-full'):
                    ui.button('アカウント追加')
                    ui.space()
                    ui.button('データベースダウンロード', color='teal', on_click=lambda: all_vector_data.download_acocunts_vectors(table=users_table))

        with ui.step('チャットデータベース', icon='settings'):
            with ui.column(align_items='center').classes('w-full mx-auto'):
                vector_table_options = {
                    "defaultColDef": {
                        "editable": True,
                        "minWidth": 160,
                        "resizable": True,
                        "sortable": True,
                        "headerCheckboxSelection": False,
                        "headerCheckboxSelectionFilteredOnly": True,
                        "floatingFilter": True,
                        "headerClass": "font-bold",
                    },
                    "columnDefs": [
                        {
                            'headerName': 'ID',
                            "editable": True,
                            'field': 'vector_id',
                            'filter': 'agMultiColumnFilter',
                            "checkboxSelection": True,
                            "headerCheckboxSelection": True,
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': 'ドメイン',
                            'field': 'shop_name_en',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': '商材',
                            'field': 'service',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': 'チャットボットタイプ',
                            'field': 'chat_bot_type',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': 'Q&A内容',
                            'field': 'text',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "cellEditor": "agLargeTextCellEditor",
                            "cellEditorPopup": True,
                            "cellEditorParams": {
                                "rows": 15,
                                "cols": 50
                            },
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            }
                        },
                        {
                            'headerName': '追加日付',
                            'field': 'added_date',
                            "filter": "agDateColumnFilter",
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            },
                        },
                        {
                            'headerName': '追加時間',
                            'field': 'added_time',
                            'filter': 'agMultiColumnFilter',
                            'floatingFilter': True,
                            "filter": True,
                            "filterParams": {
                                "maxNumConditions": 50,
                                "numAlwaysVisibleConditions": 2,
                                "defaultJoinOperator": "OR",
                                'buttons': ["reset"],
                            }
                        },
                    ],
                    "rowData": [],
                    "suppressDragLeaveHidesColumns": True,
                    "rowModelType": "clientSide",
                    "rowSelection": "multiple",
                    "rowMultiSelectWithClick": True,
                    "suppressRowDeselection": False,
                    "suppressRowClickSelection": False,
                    "groupSelectsChildren": True,
                    "groupSelectsFiltered": True,
                    "animateRows": True,
                    "alwaysShowHorizontalScroll": True,
                    "localeText": localeText,
                }
                vector_table = ui.aggrid(vector_table_options, theme='material', auto_size_columns=True).classes('h-[calc(100vh-300px)]')

                class AddVector:
                    def __init__(self):
                        self.shop_name_en = ''
                        self.service = ''
                        self.chat_bot_type = ''
                        self.text = ''
                        self.added_date = ''
                        self.added_time = ''
                        self.id = ''

                    async def add_vector(self, shop_name_en: str, namespace: str, qa_text: str, service: str, vector_table: ui.aggrid):
                        if not shop_name_en or len(shop_name_en) < 1:
                            ui.notify("ドメインを入力してください！", type="warning")
                            return
                        
                        if not service or len(service) < 1:
                            ui.notify("商材を入力してください！", type="warning")
                            return
                        
                        if not namespace or len(namespace) < 1:
                            ui.notify("Q&Aデータをベース入力してください！", type="warning")
                            return

                        if not qa_text or len(qa_text) < 1:
                            ui.notify("Q&A内容を入力してください！", type="warning")
                            return

                        dialog_add_vector.close()
                        flash_screen(progress=0, progress_text=0, status='open')

                        list_added_id = await run.io_bound(add_vector_data, namespace, qa_text, service)
                        await asyncio.sleep(1)
                        new_added_data = await run.io_bound(get_specific_vector_data, namespace, list_added_id)
                        new_added_data['shop_name_en'] = shop_name_en
                        # new_added_data['account_id'] = ??? Need to be rectify
                        new_added_data['vector_db_namespace'] = namespace

                        df_concat = pd.concat([all_vector_data.df_all_vector_data, new_added_data])
                        all_vector_data.df_all_vector_data = df_concat
                       
                        flash_screen(progress=1, progress_text=100)
                        vector_table.run_grid_method("setGridOption", "rowData",  all_vector_data.df_all_vector_data.to_dict("records"), timeout=10)
                        # vector_table.run_grid_method('ensureIndexVisible', df_concat.index[-1], 'bottom')
                        # grid_target.run_grid_method('flashCells', { "columns": [column_name] })
                        await asyncio.sleep(2.5)
                        flash_screen(status='close')
                        ui.notify('Q&Aの追加が完了しました！', type='positive')

                add_vector_object = AddVector()

                class RemoveVector:
                    def __init__(self):
                        self.shop_name_en = ''
                        self.service = ''
                        self.chat_bot_type = ''
                        self.text = ''
                        self.added_date = ''
                        self.added_time = ''
                        self.id = ''

                    async def remove_vector(self, vector_table: ui.aggrid):
                        selected_vectors = await ui.run_javascript(f'getElement({vector_table.id}).api.getSelectedNodes().map(node => node.data.vector_id)')
                        selected_vectors_index = [item for item in selected_vectors]

                        if not selected_vectors_index or len(selected_vectors_index) < 1:
                            ui.notify("削除したいQ&A内容を選択してください！", type="warning")
                            return

                        df_all_vector_data_temp = all_vector_data.df_all_vector_data.copy(deep=True)
                        df_selected_rows = df_all_vector_data_temp[df_all_vector_data_temp['vector_id'].isin(selected_vectors_index)]
                        list_namespaces = df_selected_rows['vector_db_namespace'].unique().tolist()

                        delete_prompt = await dialog_remove_vector
                        if delete_prompt == '削除':
                            flash_screen(progress=0, progress_text=0, status='open')

                            for index, namespace in enumerate(list_namespaces):
                                df_one_namespace = df_selected_rows[df_selected_rows['vector_db_namespace'] == namespace]
                                delete_id = df_one_namespace['vector_id'].unique().tolist()

                                delete_is_success = await run.io_bound(remove_vector, delete_id, namespace)
                                await asyncio.sleep(1)
                                if delete_is_success:
                                    index_tobe_deleted = all_vector_data.df_all_vector_data[all_vector_data.df_all_vector_data['vector_id'].isin(delete_id)].index
                                    new_df_all_vector_data = all_vector_data.df_all_vector_data.drop(index_tobe_deleted)
                                    all_vector_data.df_all_vector_data = new_df_all_vector_data

                                progress_value = float((index + 1) / len(list_namespaces))
                                flash_screen(progress=progress_value, progress_text=int(progress_value*100))

                            vector_table.run_grid_method("setGridOption", "rowData", all_vector_data.df_all_vector_data.to_dict("records"), timeout=10)
                            
                            # vector_table.run_grid_method('ensureIndexVisible', df_concat.index[-1], 'bottom')
                            # grid_target.run_grid_method('flashCells', { "columns": [column_name] })
                            await asyncio.sleep(2.5)
                            flash_screen(status='close')
                
                remove_vector_object = RemoveVector()

                with ui.dialog().props('persistent transition-show="scale" transition-hide="scale"') as dialog_add_vector, ui.card().classes('!max-w-full'):
                    with ui.column().classes('w-full'):
                        ui.label('Q&Aを追加')
                        with ui.row():
                            with ui.column().classes('h-full'):
                                with ui.row(align_items='baseline').classes('w-full'):
                                    ui.label('ドメイン：')
                                    ui.space()
                                    shop_name_en_select = ui.select(options=[]).props('outlined').classes('w-64')
                                with ui.row(align_items='baseline').classes('w-full'):
                                    ui.label('商材：')
                                    ui.space()
                                    service_input = ui.input().props('outlined').classes('w-64')
                                with ui.row(align_items='baseline').classes('w-full'):
                                    ui.label('Q&Aデータベース：')
                                    ui.space()
                                    database_name_select = ui.select(options=[]).props('outlined').classes('w-64')
                                with ui.row(align_items='center').classes('w-full'):
                                    ui.label('Q&A内容：')
                                    ui.space()
                                    qa_text_input = ui.textarea().props('clearable outlined input-class=h-full').classes('w-64')
                        with ui.row(align_items='center').classes('w-full'):
                            ui.space()
                            ui.button('キャンセル', on_click=lambda: dialog_add_vector.close())
                            ui.button('追加', on_click=lambda: add_vector_object.add_vector(
                                    shop_name_en=shop_name_en_select.value,
                                    namespace=database_name_select.value,
                                    qa_text=qa_text_input.value,
                                    service=service_input.value,
                                    vector_table=vector_table
                                )
                            )

                with ui.dialog().props('persistent transition-show="scale" transition-hide="scale"') as dialog_remove_vector, ui.card().classes('!max-w-full'):
                    ui.label('選択したQ&Aの内容を削除しますか？')
                    with ui.row().classes('w-full'):
                        ui.space()
                        ui.button('削除', on_click=lambda: dialog_remove_vector.submit('削除'))
                        ui.button('キャンセル', on_click=lambda: dialog_remove_vector.close())

                with ui.row(align_items='center').classes('w-full'):
                    ui.button('編集')
                    ui.space()
                    ui.button('Q&A追加', color='teal', on_click=lambda: dialog_add_vector.open())
                    ui.button('Q&A削除', color='red', on_click=lambda: remove_vector_object.remove_vector(vector_table=vector_table))


    startup_element.clear()