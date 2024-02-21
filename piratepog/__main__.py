import json
from pathlib import Path

import click

from piratepog import Processor, UserConfig


@click.command()
@click.argument("types_json", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--show-enum-stubs", is_flag=True, default=False)
def main(types_json: Path, input_file: Path, show_enum_stubs: bool):
    """
    piratepog
    """
    config = UserConfig(show_enum_stubs=show_enum_stubs)

    processor = Processor(type_data=json.load(types_json.open()), config=config)
    result = processor.process(data=json.load(input_file.open()), decent_tree=[], recurse_into=True)

    click.echo(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
