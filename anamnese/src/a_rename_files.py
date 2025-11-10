import os
import pandas as pd
import yaml


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
        camera: get_files_list(config_general["paths"][camera])
        for camera in ["flir", "vue", "canon"]
    }


def assert_lengths_equal(files_dict):
    """Ensure all file lists have the same length."""
    lengths = {camera: len(files) for camera, files in files_dict.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(
            f"File counts do not match! {', '.join(f'{camera.upper()}: {count} files' for camera, count in lengths.items())}"
        )


def rename_canon_files(files_dict):
    """Rename Canon files to match the names of FLIR files."""
    files_dict["canon_new"] = [
        os.path.join(os.path.dirname(file_canon), os.path.basename(file_reference))
        for file_reference, file_canon in zip(files_dict["flir"], files_dict["canon"])
    ]
    import ipdb
    ipdb.set_trace()
    for old_name, new_name in zip(files_dict["canon"], files_dict["canon_new"]):
        os.rename(old_name, new_name)
    files_dict["canon"] = files_dict["canon_new"]
    del files_dict["canon_new"]
    return files_dict


def rename_files_to_standard(files_dict, config_anamnese):
    """Rename files to a standardized format."""
    pessoa = input(
        "Qual pessoa está gravando (Isabela -> p001, Thyago -> p002, Natalia -> p003): "
    )
    df = pd.read_excel(config_anamnese["sentence"], sheet_name=None)
    # Implement the logic for renaming files based on the DataFrame `df`.


def main(config_anamnese, config_general):
    """Main function to orchestrate file renaming."""
    files_dict = get_files(config_general)
    assert_lengths_equal(files_dict)
    files_dict = rename_canon_files(files_dict)
    rename_files_to_standard(files_dict, config_anamnese)


if __name__ == "__main__":
    config_anamnese = load_config("anamnese/config/anamnese.yaml")
    config_general = load_config("config/general.yaml")
    main(config_anamnese, config_general)
