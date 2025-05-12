import os
from typing import Optional, Dict, List

import pandas as pd

from supabase import create_client, Client
from pydantic import BaseModel

supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

class User(BaseModel):
    shop_name_en: str
    shop_name_jp: str
    shop_products: Optional[str] = None
    disabled: Optional[bool] = None
    bot_name: Optional[str] = None
    vector_db_namespace: Optional[str] = None
    openai_chat_prompt: Optional[str] = None
    openai_speech_prompt: Optional[str] = None
    first_message: Optional[str] = None

def get_shop_information(shop_name_en: str) -> Optional[User]:
    """
    Query the 'users' table in Supabase to fetch user info by shop_name.
    """
    response = supabase.table("users").select("*").eq("shop_name_en", shop_name_en).execute()

    data = response.data
    if not data:
        return None

    row = data[0]
    user = User(
        shop_name_en=row.get('shop_name_en'),
        shop_name_jp=row.get('shop_name_jp'),
        shop_products=row.get('shop_products'),
        disabled=row.get("disabled", False),
        bot_name=row.get('bot_name'),
        vector_db_namespace=row.get('vector_db_namespace'),
        openai_chat_prompt=row.get('openai_chat_prompt'),
        openai_speech_prompt=row.get('openai_speech_prompt'),
        first_message=row.get('first_message')
    )

    return user

def get_table_data(table_name : str) -> pd.DataFrame:
    response = supabase.table(table_name).select("*").execute()
    data = response.data
        
    df_data = pd.DataFrame(data)

    return df_data

def update_table_data(table_name: str, filter_conditions: dict, new_values: dict) -> pd.DataFrame:
    """
    Update rows in a Supabase table that match the filter conditions with new values.

    Args:
        table_name (str): The name of the table to update.
        filter_conditions (dict): A dictionary specifying which rows to update 
                                  (e.g., {"id": 1}).
        new_values (dict): A dictionary containing the new values 
                           to set for the matching rows (e.g., {"name": "John"}).

    Returns:
        pd.DataFrame: A DataFrame containing the updated rows.
    """
    # Execute the update operation
    response = supabase.table(table_name).update(new_values).match(filter_conditions).execute()
    
    # Check for errors (the structure of response may vary depending on your version)
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error updating data: {response.error.message}")
    
    # Retrieve the data from the response; adjust depending on the response format
    data = response.data if hasattr(response, 'data') else response.get('data', [])
    
    # Convert the result into a pandas DataFrame (optional)
    return pd.DataFrame(data)