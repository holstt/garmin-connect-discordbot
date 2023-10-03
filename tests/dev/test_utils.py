import json
import logging
from pathlib import Path
from typing import Any, Protocol, Type, TypeVar

from src.domain.models import DatePeriod
from src.infra.garmin.dtos.garmin_stress_response import GarminDto
from src.infra.garmin.garmin_api_adapter import dto_to_endpoint
from src.infra.garmin.garmin_endpoints import GarminEndpoint
from src.utils import to_YYYYMMDD

logger = logging.getLogger(__name__)


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
# TODO: Generate some fake test data for repo
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
