import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from .pricing_pipeline import FEATURE_COLUMNS


class ComparablesFinder:
    """یافتن فایل‌های مشابه (comparables) با شباهت برداری روی ویژگی‌های استانداردشده.

    در نسخه بعدی می‌توان به‌جای NearestNeighbors این‌جا، جست‌وجوی شباهت را
    مستقیماً در PostgreSQL با ستون feature_embedding (pgvector) انجام داد.
    """

    def __init__(self, n_neighbors: int = 5) -> None:
        self.n_neighbors = n_neighbors
        self.scaler = StandardScaler()
        self.nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
        self._ids: list[str] = []

    def fit(self, df: pd.DataFrame, id_col: str = "id") -> None:
        X = self.scaler.fit_transform(df[FEATURE_COLUMNS])
        self.nn.fit(X)
        self._ids = df[id_col].astype(str).tolist()

    def find(self, target: pd.DataFrame) -> list[list[dict]]:
        X = self.scaler.transform(target[FEATURE_COLUMNS])
        distances, indices = self.nn.kneighbors(X, n_neighbors=self.n_neighbors)
        return [
            [
                {"id": self._ids[i], "similarity": float(1 - d)}
                for i, d in zip(idx_row, dist_row)
            ]
            for idx_row, dist_row in zip(indices, distances)
        ]
