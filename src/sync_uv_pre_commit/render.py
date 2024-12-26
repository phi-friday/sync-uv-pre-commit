from __future__ import annotations

from pathlib import Path

import jinja2

from sync_uv_pre_commit.toml import read_pyproject


def generate_script() -> None:
    """Generate the script.py file."""
    pyproject_file = Path(__file__).parent.parent.parent / "pyproject.toml"
    export_template_file = Path(__file__).parent / "export.py.j2"
    export_script_file = Path(__file__).parent / "export.py"
    output = Path(__file__).parent.parent.parent / "script.py"

    pyproject = read_pyproject(pyproject_file)
    with export_template_file.open("r") as f:
        template = jinja2.Template(f.read())
    with export_script_file.open("r") as f:
        export_script = f.read()

    script = template.render(
        requires_python=">=3.13",
        dependencies=pyproject["project"]["dependencies"],
        export_script=export_script,
    )
    with output.open("w+") as f:
        f.write(script)
