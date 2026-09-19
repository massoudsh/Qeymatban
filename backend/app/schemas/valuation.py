from pydantic import BaseModel, Field


class PropertyFeatures(BaseModel):
    """ویژگی‌های ورودی یک ملک برای ارزش‌گذاری (باید با FEATURE_COLUMNS همخوان باشد)."""

    area_sqm: float
    year_built: int
    floor: int
    total_floors: int
    rooms: int
    has_parking: bool = False
    has_elevator: bool = False
    has_storage: bool = False
    renovated: bool = False
    light_score: int = Field(ge=1, le=5)
    view_score: int = Field(ge=1, le=5)
    access_score: int = Field(ge=1, le=5)


class ValuationRequest(PropertyFeatures):
    """اطلاعات ملک که از فرم ارزش‌گذاری وارد می‌شود."""

    neighborhood: str = Field(min_length=1, max_length=100)
    city: str = Field(default="تهران", max_length=100)
    title: str = Field(default="ملک جدید", max_length=200)


class ComparableResult(BaseModel):
    id: str
    similarity: float


class ValuationResponse(BaseModel):
    price_low: float
    price_mid: float
    price_high: float
    feature_contributions: dict[str, float]
    comparables: list[ComparableResult]
