#!/bin/bash

gource ./ --user-image-dir images -c 1 -s 2.5 -b 000000 \
  --logo ~/Desktop/steemit-notes/steemit.svg \
  --background-image ~/Desktop/steemit-notes/tokens-opacity-12.5.png \
  --start-date '2017-01-01 00:00' \
  -1280x720 --output-ppm-stream - |\
  ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264 -preset ultrafast -pix_fmt yuv420p -crf 1 -threads 0 -bf 0 output.mp4
