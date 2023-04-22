#!/bin/bash
TARGET=$1
HASH_PATH=$2
ls_output=$(ls $TARGET)

PREV_HASH=$(cat $HASH_PATH)
CURR_HASH=$(echo -n "$ls_output" | sha256sum | awk '{ print $1 }')

echo "from hash-poll: "
CURR_USER=$(id -u)
echo $CURR_USER

if ! [ "$PREV_HASH" = "$CURR_HASH" ]; then
  echo "Changes have been detected within the $TARGET directory, reparsing uploads"
  
  echo "$3"
  eval $3

  echo -n $CURR_HASH > $HASH_PATH
else
  echo "No changes have been detected within the $TARGET directory, skipping parsing."
fi