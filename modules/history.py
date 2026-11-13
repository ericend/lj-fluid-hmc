from dataclasses import dataclass, field

import numpy as np


@dataclass
class History:
    T: list[float] = field(default_factory=list)
    U: list[float] = field(default_factory=list)
    K: list[float] = field(default_factory=list)
    P: list[float] = field(default_factory=list)
    accepted: list[bool] = field(default_factory=list)

    def record(self, state) -> None:
        self.T.append(state.T)
        self.U.append(state.U)
        self.K.append(state.K)
        self.P.append(state.P)
        self.accepted.append(state.accepted)

    def last(self, name: str) -> float:
        return getattr(self, name)[-1]

    def as_dict(self) -> dict[str, np.ndarray]:
        return {k: np.asarray(v) for k, v in vars(self).items()}
