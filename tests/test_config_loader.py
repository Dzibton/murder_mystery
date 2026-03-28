import pytest
import yaml
from config_loader import load_config, ConfigError


def test_load_valid_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "characters": ["Alice", "Bob"],
        "questions": [
            {"id": "name", "text": "Your name?", "type": "dropdown"},
            {"id": "why", "text": "Why?", "type": "text"},
        ]
    }))
    config = load_config(str(config_file))
    assert config["characters"] == ["Alice", "Bob"]
    assert len(config["questions"]) == 2


def test_missing_config_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "missing.yaml"))


def test_missing_characters_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"questions": []}))
    with pytest.raises(ConfigError, match="characters"):
        load_config(str(config_file))


def test_missing_questions_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"characters": ["Alice"]}))
    with pytest.raises(ConfigError, match="questions"):
        load_config(str(config_file))


def test_missing_name_question_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "characters": ["Alice"],
        "questions": [{"id": "why", "text": "Why?", "type": "text"}]
    }))
    with pytest.raises(ConfigError, match="name"):
        load_config(str(config_file))
