#!/usr/bin/python3

# TODO 
# This is work in progress.
# Ideally foam entries should be handled as dataclasses which automaticaly handle any parsing and hold additional data like dimensions

import numpy as np
import dataclasses
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)  # frozen: read only, to change: dataclasses.replace(instance, attr=newValue)
class Field:
    """
    class to set attributes of foam volScalarFields and volVectorFields
    """
    directory: str  # for example U, p
    scalarField: bool  # volScalarField or volVectorField
    uniform: bool  # uniform, nonuniform
    values: np.ndarray  # of shape (n) or (3, n)
    fieldLength: int = field(init=False)

    def __post_init__(self):
        if not isinstance(self.values, np.ndarray):
            object.__setattr__(self, "values", np.array(self.values))
        if len(self.values) > 1:
            print(len(self.values))
            object.__setattr__(self, 'fieldLength', np.shape(self.values)[-1])
        else:
            print("singleVlaue")
            object.__setattr__(self, "fieldLength", 0)

    def __len__(self):
        return self.fieldLength

    # as the dataclass is frozen, we need to use functions to change values. As a new instance is returned, the usage of the function has to be assigned fld = fld.changeValues(XXXX)
    def changeValues(self, newValues: list[float]) -> "Field":
        return dataclasses.replace(self, values=newValues)

    def getType(self) -> str:
        if self.scalarField:
            return "volScalarField"
        else:
            return "volVectorField"
