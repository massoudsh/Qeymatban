from pydantic import BaseModel, Field


class PropertyFeatures(BaseModel):
    """ویژگی‌های ورودی یک ملک برای ارزش‌گذاری (باید با FEATURE_COLUMNS همخوان باشد)."""

    area_sqm: float = Field(gt=0, le=5000)
    year_built: int = Field(ge=1300, le=1500)
    floor: int = Field(ge=-5, le=200)
    total_floors: int = Field(ge=1, le=200)
    rooms: int = Field(ge=0, le=30)
    has_parking: bool = False
    has_elevator: bool = False
    has_storage: bool = False
    renovated: bool = False
    light_score: int = Field(ge=1, le=5)
    view_score: int = Field(ge=1, le=5)
    access_score: int = Field(ge=1, le=5)


class ValuationRequest(PropertyFeatures):
    """اطلاعات ملک که از فرم ارزش‌گذاری وارد می‌شود."""

    neighborhood: str = Field(default="نامشخص", min_length=1, max_length=100)
    city: str = Field(default="تهران", max_length=100)
    title: str = Field(default="ملک جدید", max_length=200)


class ComparableResult(BaseModel):
    id: str
    similarity: float


class ValuationResponse(BaseModel):
    price_low: float
    price_mid: float
    price_high: float
    confidence_level: float
    model_version: str
    feature_contributions: dict[str, float]
    comparables: list[ComparableResult]
    valuation_id: str | None = None


class ModelStatusResponse(BaseModel):
    ready: bool
    model_version: str | None = None
