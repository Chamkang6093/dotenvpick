#!/bin/bash

usage() {
  echo "Usage: $0 -f <env_file> -v <variable_name> [-v <variable_name> ...]" >&2
  echo "       $0 <env_file> <variable_name> [<variable_name> ...]" >&2
  echo "Example: $0 prod/.env DB_HOST DB_PORT" >&2
}

# Parse option or positional arguments.
env_file=""
var_names=()

# Parse named options, such as -f prod/.env -v DB_HOST -v DB_PORT.
# Each colon requires a value for the preceding option (-f or -v).
# getopts stores the option name in opt and its value in OPTARG.
# OPTIND is the 1-based index of the next argument to process.
while getopts "f:v:" opt; do
  case "$opt" in
    f) env_file="$OPTARG"       # -f option (.env file path)
    ;;
    v) var_names+=("$OPTARG")   # Repeat -v to request multiple variables.
    ;;
    *)
      usage
      exit 1
    ;;
  esac
done
shift "$((OPTIND - 1))"

# Parse a file path followed by variable names when no named options were supplied.
if [ "$#" -ge 2 ] && [ -z "$env_file" ] && [ "${#var_names[@]}" -eq 0 ]; then
  env_file="$1"
  # Remove the file path so the remaining arguments are variable names.
  shift
  var_names=("$@")
elif [ "$#" -ne 0 ]; then
  usage
  exit 1
fi

# Require a nonempty .env file path and at least one variable name.
if [ -z "$env_file" ] || [ "${#var_names[@]}" -eq 0 ]; then
  usage
  exit 1
fi

if [ ! -f "$env_file" ]; then
  echo "Error: Environment file '$env_file' not found." >&2
  exit 1
fi

# Collect matching KEY=value lines so missing variables fail before any output is written.
env_lines=()
for var_name in "${var_names[@]}"; do
  if [ -z "$var_name" ]; then
    usage
    exit 1
  fi

  env_line=$(grep -E "^$var_name=" "$env_file" 2>/dev/null)
  if [ -z "$env_line" ]; then
    echo "Error: Variable '$var_name' not found in '$env_file'." >&2
    exit 1
  fi
  env_lines+=("$env_line")
done

# Print one KEY=value line per requested variable, preserving its original name.
printf '%s\n' "${env_lines[@]}"
