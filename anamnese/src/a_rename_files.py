import os
import pandas as pd
import yaml
from pathlib import Path
from tqdm import tqdm

def load_config(path):
    """Load a YAML configuration file."""
    with open(path, "r") as file:
        return yaml.safe_load(file)


def get_files_list(path, extensions=(".mp4", ".mov")):
    """Get a sorted list of files with specific extensions in a directory."""
    return sorted(
        (
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.lower().endswith(extensions)
        ),
        key=os.path.getmtime,
    )


def get_files(config_general):
    """Retrieve lists of files for each camera type."""
    return {
        camera: get_files_list(Path(config_general["paths"][camera]))
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
        for file_reference, file_canon in zip(files_dict["flir"], files_dict[f"canon_{camera_name}"])
    ]

    for old_name, new_name in zip(files_dict[f"canon_{camera_name}"], files_dict[f"canon_{camera_name}_new"]):
        if old_name != new_name:
            os.rename(old_name, new_name)

    files_dict[f"canon_{camera_name}"] = files_dict[f"canon_{camera_name}_new"]
    del files_dict[f"canon_{camera_name}_new"]
    return files_dict

def get_person_code():
    """Prompt user for person code."""
    pessoa = None
    while pessoa not in ["p001", "p002", "p003"]:
        pessoa = input(
            "Qual pessoa está gravando (Isabela -> p001, Thyago -> p002, Natalia -> p003): "
        )
    return pessoa

def get_anamnese_dataframe(config_anamnese):
    """Load the anamnese sentences dataframe."""
    columns = ['ID', 'ID Sentenca']
    dfs = pd.read_excel(Path(config_anamnese["sentence"]), sheet_name=None)
    df = pd.DataFrame()
    for sub_df in dfs.values():
        df = pd.concat([df, sub_df[columns]], ignore_index=True)
    return df

def get_select_files_dataframe(files):
    files_df = pd.DataFrame(
        [
            (
                Path(file).stem.split(".")[0],
                file,
                True,
            ) for file in files
        ],
        columns=['file_id', 'file_path', 'is_selected'],
    )
    for index, row in files_df.iterrows():
        file_id = row['file_id']
        if file_id[-1].isalpha():
            files_df.at[index-1, 'is_selected'] = False

    return files_df

def rename_files_to_standard(files_dict, config_anamnese, config_general):
    """Rename files to a standardized format."""
    pessoa = get_person_code()
    df = get_anamnese_dataframe(config_anamnese)
    for camera, files in tqdm(files_dict.items()):
        df = get_select_files_dataframe(files)

        for file_id, file_path in files:

            import ipdb
            ipdb.set_trace()
            take="t000"
            file_id = Path(file).stem.split(".")[0]

            if file_id[-1].isalpha():
                file_id = file_id[:-1]

            matching_id = df[df["ID"] == file_id]["ID Sentenca"].squeeze()

            if matching_id:
                root_folder = Path(config_anamnese["root_folder"]) / matching_id
                root_folder.mkdir(parents=True, exist_ok=True)
                new_name = f"{matching_id}_{pessoa}_{camera}_{take}.mp4"
                new_file_path = root_folder / new_name

                while new_file_path.exists():
                    take = f"t{int(take[1:]) + 1:03d}"
                    camera_id = config_general["camera"][camera]
                    new_name = f"{matching_id}_{pessoa}_{camera_id}_{take}.mp4"
                    new_file_path = root_folder / new_name

                os.rename(file, new_file_path)
            else:
                raise ValueError(f"No matching sentence ID found for file ID: {file_id}")
    import ipdb
    ipdb.set_trace()

def main(config_anamnese, config_general):
    """Main function to orchestrate file renaming."""
    files_dict = get_files(config_general)
    assert_lengths_equal(files_dict)
    files_dict = rename_canon_files(files_dict, "front")
    files_dict = rename_canon_files(files_dict, "side")
    rename_files_to_standard(files_dict, config_anamnese, config_general)


if __name__ == "__main__":
    config_anamnese = load_config("anamnese/config/anamnese.yaml")
    config_general = load_config("config/general.yaml")
    main(config_anamnese, config_general)
