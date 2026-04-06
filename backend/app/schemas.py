from pydantic import BaseModel
from typing import List


class PredictRequest(BaseModel):
    sequence: str


class PredictionItem(BaseModel):
    ecNumber: str
    probability: float
    source: str


class ResidueItem(BaseModel):
    aa: str
    value: float


class FragmentItem(BaseModel):
    id: int
    label: str
    residues: List[ResidueItem]


class ExternalSequenceItem(BaseModel):
    id: int
    source: str
    ecNumber: str
    rank: int
    similarity: float
    sequence: str
    originalSequence: str
    probabilityOpus: float
    probabilityEsm: float


class ExternalSequenceGroup(BaseModel):
    ecNumber: str
    items: List[ExternalSequenceItem]


class PredictResponse(BaseModel):
    predictions: List[PredictionItem]
    fragments: List[FragmentItem]
    externalSequenceGroups: List[ExternalSequenceGroup]