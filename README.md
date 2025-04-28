# A Testbed for Nerf 3D Modeling and Visualzation in Digital Twin

We construct a testbed to run a workflow that generates 3D objects from live camera streams and pushing those objects into a virtual environment, e.g. Unity, for digital twin. The goal is to understand characteristics of the workflow and relationship of the characteristics into system, technology characteristics.

## Docker

Tasks in the workflow are packaged using Docker for their execution on a computing node. See each subdirectory under [docker](docker/) contains Dockerfile for each task.