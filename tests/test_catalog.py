import os
import pytest

import xrdimageutil as xiu

@pytest.fixture
def valid_project():
    return xiu.Project(project_path="data/singh")