import pandas as pd
import os
from tqdm import tqdm
import shutil

ORG_FILENAME = 'anamnese_sentencas_augumentadas.xlsx'
CORRECTED_FILENAME = 'anamnese_sentencas_corrigidas.xlsx'

OLD_FOLDER_NAME = "anamnese"
NEW_FOLDER_NAME = f"{OLD_FOLDER_NAME}_renomeada"

DIR_PATH = f'D:/CCD-TAAL/{OLD_FOLDER_NAME}'


def read_excel_sheets(filename):
    return pd.read_excel(filename, sheet_name=None)

def read_data():
    df_original = read_excel_sheets(ORG_FILENAME)
    df_corrected = read_excel_sheets(CORRECTED_FILENAME)
    return df_original, df_corrected

def get_incosistencies(df_original, df_corrected):
    inconsistencies = {}
    for sheet_name in df_original.keys():
        df_orig = df_original[sheet_name]
        df_corr = df_corrected[sheet_name]

        for row in range(len(df_orig)):
            id_orig = df_orig.at[row, 'ID']
            id_corr = df_corr.at[row, 'ID']
            if isinstance(id_orig, str) and id_orig != id_corr:
                inconsistencies[id_orig] = id_corr
    return inconsistencies

def add_txt(old_path, new_path=None, txt_path = 'renamed_files_log.txt'):
    with open(txt_path, 'a', encoding='utf-8') as f:
        f.write(f"{old_path};{new_path}\n")

def move_single_file(filename, new_id, file_id, root):
    new_filename = filename.replace(file_id, new_id)
    old_path = os.path.join(root, filename)
    root = root.replace(OLD_FOLDER_NAME, NEW_FOLDER_NAME)
    new_path = os.path.join(root, new_filename)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    try:
        shutil.move(old_path, new_path)
        add_txt(old_path, new_path)
        print(f"Moved: {old_path} -> {new_path}")
    except Exception as e:
        print(f"Failed to move {old_path} -> {new_path}: {e}")
    
def move_files(inconsistencies):
    for root, dirs, files in os.walk(DIR_PATH):
        for filename in tqdm(files):
            file_id = filename.split('.')[0]
            new_id = inconsistencies.get(file_id, None)
            if new_id:
                move_single_file(filename, new_id, file_id, root)
            else:
                file_id = file_id[:-1]
                new_id = inconsistencies.get(file_id, None)
                if new_id:
                    move_single_file(filename, new_id, file_id, root)
                else:
                    old_path = os.path.join(root, filename)
                    add_txt(old_path, new_path=None, txt_path='not_renamed_files_log.txt')
            
def main(): 
    df_original, df_corrected = read_data()
    inconsistencies = get_incosistencies(df_original, df_corrected)
    move_files(inconsistencies)
    
if __name__ == "__main__":
    main()