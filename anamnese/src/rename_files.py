import os
import shutil
import pandas as pd
import yaml
from pathlib import Path
from tqdm import tqdm


def load_config(path):
    """Load a YAML configuration file."""
    with open(path, "r") as file:
        return yaml.safe_load(file)


def get_files_single_camera(path, extensions=(".mp4", ".mov")):
    """Get a sorted list of files with specific extensions in a directory."""
    return sorted(
        (
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.lower().endswith(extensions)
        ),
        key=os.path.getmtime,
    )


def get_files_all_cameras(config_general):
    """Retrieve lists of files for each camera type."""
    return {
        camera: get_files_single_camera(Path(config_general["paths"][camera]))
        for camera in config_general["paths"].keys()
    }


def assert_lengths_equal(files_dict):
    """Ensure all file lists have the same length."""
    lengths = {camera: len(files) for camera, files in files_dict.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(
            f"File counts do not match! {', '.join(f'{camera.upper()}: {count} files' for camera, count in lengths.items())}"
        )


def rename_canon_files(files_dict, camera_name):
    """Rename Canon files to match the names of FLIR files."""
    files_dict[f"canon_{camera_name}_new"] = [
        str(Path(file_canon).parent / Path(file_reference).name)
        for file_reference, file_canon in zip(
            files_dict["flir"], files_dict[f"canon_{camera_name}"]
        )
    ]

    for old_name, new_name in zip(
        files_dict[f"canon_{camera_name}"], files_dict[f"canon_{camera_name}_new"]
    ):
        if old_name != new_name:
            os.rename(old_name, new_name)
            add_logs(old_name, new_name, log_file="anamnese/logs/rename_log_canon.txt")

    files_dict[f"canon_{camera_name}"] = files_dict[f"canon_{camera_name}_new"]
    del files_dict[f"canon_{camera_name}_new"]
    return files_dict


def get_person_code(config_general):
    """Prompt user for person code."""
    reverse_person_codes = {v: k for k, v in config_general["pessoa"].items()}
    pessoa = None
    while pessoa not in list(reverse_person_codes):
        pessoa = input(f"Qual pessoa está gravando {list(reverse_person_codes)}: ")
        print(f"Pessoa selecionada: {pessoa}")
    return reverse_person_codes[pessoa]


def check_selected_files_df(df_files):
    for index, _ in df_files[~df_files.is_selected].iterrows():
        upper_index = index - 10 if index - 10 >= 0 else 0
        lower_index = index + 10 if index + 10 < len(df_files) else len(df_files) - 1
        context = df_files.iloc[upper_index : lower_index + 1]
        print(context)


def get_select_files_dataframe(files):
    files_df = pd.DataFrame(
        [
            (
                Path(file).stem.split(".")[0],
                file,
                True,
            )
            for file in files
        ],
        columns=["file_id", "file_path", "is_selected"],
    )
    for index, row in files_df.iterrows():
        file_id = row["file_id"]
        if file_id[-1].isalpha():
            file_id_root = file_id[:-1]
            until_current = files_df[:index]
            older_file_ids = [
                r.file_id
                for r in until_current.itertuples()
                if r.file_id.startswith(file_id_root)
            ]
            for older_id in older_file_ids:
                files_df.loc[files_df["file_id"] == older_id, "is_selected"] = False

    return files_df


def add_logs(old_file_name, new_file_name, log_file="anamnese/logs/rename_log.txt"):
    """Append rename actions to a log file."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    date = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as log:
        log.write(f"{date};{old_file_name};{new_file_name}\n")


def rename_files_to_standard(files_dict, config_anamnese, config_general):
    """Rename files to a standardized format."""
    person = get_person_code(config_general)
    for camera, files in tqdm(files_dict.items()):
        camera_id = config_general["camera"][camera]
        df_files = get_select_files_dataframe(files)
        num_files_with_errors = len(df_files[~df_files.is_selected])
        num_files_without_errors = len(df_files[df_files.is_selected])
        num_files_already_processed_without_errors = 0
        # TODO continuar a logica para pegar o numero de arquivos
        for file_id, file_path, is_selected in df_files.itertuples(index=False):
            take = "t000"
            file_id = Path(file_path).stem.split(".")[0]
            try:
                if file_id[-1].isalpha():
                    file_id = file_id[:-1]
                root_folder_str = (
                    config_anamnese["root_folder"]
                    if is_selected
                    else config_anamnese["root_folder_errors"]
                )
                root_folder = Path(root_folder_str) / file_id
                root_folder.mkdir(parents=True, exist_ok=True)
                new_name = f"{file_id}_{person}_{camera_id}_{take}.mp4"
                new_file_path = root_folder / new_name

                while new_file_path.exists():
                    take = f"t{int(take[1:]) + 1:03d}"
                    new_name = f"{file_id}_{person}_{camera_id}_{take}.mp4"
                    new_file_path = root_folder / new_name

                shutil.copy(file_path, new_file_path)
                add_logs(
                    file_path,
                    new_file_path,
                )
            except:
                print(f"Error processing file ID: {file_id}")
                import ipdb

                ipdb.set_trace()


def main(config_anamnese, config_general):
    """Main function to orchestrate file renaming."""
    files_dict = get_files_all_cameras(config_general)
    assert_lengths_equal(files_dict)
    files_dict = rename_canon_files(files_dict, "front")
    files_dict = rename_canon_files(files_dict, "side")
    rename_files_to_standard(files_dict, config_anamnese, config_general)


if __name__ == "__main__":
    config_anamnese = load_config("anamnese/config/anamnese.yaml")
    config_general = load_config("config/general.yaml")
    main(config_anamnese, config_general)
