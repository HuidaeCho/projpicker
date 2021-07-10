import setuptools

with open("README.md") as f:
    long_description = f.read().rstrip()

with open("projpicker/VERSION") as f:
    version = f.read().rstrip()

setuptools.setup(
    name="projpicker",
    version=version,
    license="GPLv3+",
    author="Huidae Cho and Owen Smith",
    author_email="grass4u@gmail.com",
    description="ProjPicker (projection picker) allows the user to select all projections whose extent completely contains given points, polylines, polygons, and bounding boxes. The goal is to make it easy and visual to select a desired projection by location.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HuidaeCho/projpicker",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
    package_data={"projpicker": ["VERSION", "projpicker.db"]},
    entry_points={"console_scripts": ["projpicker=projpicker:main"]},
)
