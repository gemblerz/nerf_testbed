#!/bin/bash

docker rm -f nerfbridge

  # gemblerz/nerfbridge:1.1.0-cu126-cuarc75-humble \


docker run -d \
  --name nerfbridge \
  --runtime nvidia \
  --network host \
  -v $(pwd)/tmp:/storage \
  --entrypoint /bin/bash \
  gemblerz/nerfstudio:v1.1.5-cu126-cuarc75 \
  -c "while true; do sleep 1; done"
echo "nerfbridge container started"
echo "To access the container, run:"
echo "docker exec -it nerfbridge /bin/bash"
