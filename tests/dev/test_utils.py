import json
import logging
from pathlib import Path
from typing import Any, Protocol, Type, TypeVar

import src.setup.config as config
import src.setup.dependencies as dependency_resolver
import src.setup.logging_helper as logging_helper
from src.domain.common import DatePeriod
from src.infra.garmin.garmin_api_adapter import dto_to_endpoint
from src.setup.garmin_endpoints import GarminEndpoint
from src.utils import to_YYYYMMDD

logger = logging.getLogger(__name__)


def base_setup(with_connect: bool = False):
    logging_helper.setup_logging(
        module_logger_name=__name__, base_log_level=logging.INFO
    )
    app_config = config.get_config()
    logging_helper.add_password_filter(app_config.credentials.password)

    dependencies = dependency_resolver.resolve(app_config)
    if with_connect:
        dependencies.garmin_api_client.login()
    return dependencies


# Require dto type to implement a from_json method
class FromJsonProtocol(Protocol):
    @staticmethod
    def from_json(json: Any) -> Any:
        pass


T = TypeVar("T", bound=FromJsonProtocol)

json_dir = Path("../json_data").resolve()


def save_dto_to_file(
    json_dto: Any, period: DatePeriod, endpoint: GarminEndpoint
) -> None:
    save_path = json_dir.joinpath(
        f"{endpoint.name}_{to_YYYYMMDD(period.start)}_{to_YYYYMMDD(period.end)}.json"
    ).resolve()

    with open(save_path, "w") as f:
        json.dump(json_dto, f, indent=4)

    logger.info(f"Saved json to {save_path}")


# Load dto from json file
# Loads first file that matches endpoint associated with dto type
# TODO: Generate some fake test data and save as json files in json_data folder -> test json to dto conversion
def load_dto_from_file(dto_type: Type[T]) -> T:
    if not json_dir.exists():
        raise IOError(f"Json data directory does not exist: {json_dir}")

    endpoint = dto_to_endpoint[dto_type]  # type: ignore
    pattern = f"{endpoint.name}_*.json"

    json_file = next(json_dir.glob(pattern))
    if not json_file:
        raise IOError(f"No files found with pattern: {pattern}")

    with open(json_file, "r") as f:
        json_data = json.load(f)

    dto = dto_type.from_json(json_data)

    return dto
