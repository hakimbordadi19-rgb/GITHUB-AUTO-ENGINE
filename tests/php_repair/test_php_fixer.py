from engine.php_fixer import inspect_php, repair_php


def test_valid_php():
    code = '<?php echo "Hello";'
    assert inspect_php(code)["valid"]


def test_repair_missing_semicolons():
    code = '<?php\n$name = "Mohamed"\necho $name\n'

    result = repair_php(code)

    assert result["success"]
    assert '$name = "Mohamed";' in result["fixed_code"]
    assert 'echo $name;' in result["fixed_code"]
    assert inspect_php(result["fixed_code"])["valid"]


def test_original_code_preserved():
    code = '<?php echo "Hello";'

    result = repair_php(code)

    assert result["fixed_code"] == code


def test_inspect_php_handles_missing_binary(monkeypatch):
    def fail_run(*args, **kwargs):
        raise FileNotFoundError("PHP binary not found")

    monkeypatch.setattr(
        "engine.php_fixer.subprocess.run",
        fail_run
    )

    result = inspect_php('<?php echo "Hello";')

    assert result["valid"] is False
    assert "PHP binary not found" in result["error"]
