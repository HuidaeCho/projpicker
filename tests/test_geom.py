import pytest
from projpicker.core.geom import bbox_coors


@pytest.mark.parametrize(
        "test_bbox, expected", [
            ([24.41, -124.79, 49.38, -66.91],
                [[-124.79, 49.38], [-66.91, 49.38],
                 [-66.91, 24.41], [-124.79, 24.41]]),
            ([-90, -180, 90, 180],
                [[-180, 90], [180, 90],
                 [180, -90], [-180, -90]]),
            ([59.75, 19.24, 70.09, 31.59],
                [[19.24, 70.09], [31.59, 70.09],
                 [31.59, 59.75], [19.24, 59.75]]),
            ([30.62, -85.61, 35.01, -82.99],
                [[-85.61, 35.01], [-82.99, 35.01],
                 [-82.99, 30.62], [-85.61, 30.62]])
            ]
        )
def test_bbox_coors(test_bbox, expected):
    test = bbox_coors(test_bbox)
    assert test == expected


