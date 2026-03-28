import yaml


class ConfigError(Exception):
    pass


def load_config(path="config.yaml"):
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"config.yaml not found at {path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"config.yaml is malformed: {e}")

    if not config.get("characters"):
        raise ConfigError("config.yaml must define a non-empty 'characters' list")
    if "questions" not in config:
        raise ConfigError("config.yaml must define a 'questions' list")

    ids = [q.get("id") for q in config["questions"]]
    if "name" not in ids:
        raise ConfigError("config.yaml questions must include a question with id 'name'")

    return config
