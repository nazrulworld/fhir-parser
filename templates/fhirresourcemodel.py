# -*- coding: utf-8 -*-
"""Base class for all FHIR elements. """
from typing import Optional

from pydantic import Field

from .fhirabstractmodel import FHIRAbstractModel
from .fhirtypes import Id


class FHIRResourceModel(FHIRAbstractModel):
    """ Abstract base model class for all FHIR elements.
    """
    resourceType: str = Field("FHIRAbstractResource", const=True)
    id: Optional[Id] = None

    def relative_base(self):
        """ """
        return self.resourceType

    def relative_path(self):
        if self.id is None:
            return self.relative_base()
        return "{0}/{1}".format(self.relative_base(), self.id)
