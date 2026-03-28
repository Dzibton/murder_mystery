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

    if not config or not isinstance(config, dict):
        raise ConfigError("config.yaml is empty or not a YAML mapping")

    if not config.get("characters"):
        raise ConfigError("config.yaml must define a non-empty 'characters' list")
    if "questions" not in config:
        raise ConfigError("config.yaml must define a 'questions' list")
    if not isinstance(config.get("questions"), list):
        raise ConfigError("config.yaml 'questions' must be a list")

    ids = [q.get("id") for q in config["questions"]]
    if "name" not in ids:
        raise ConfigError("config.yaml questions must include a question with id 'name'")

    return config
