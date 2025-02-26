#!/bin/bash
build() {
    local file_prefix="${is_project:+project}"
    file_prefix="${file_prefix:-assignment}"
    echo "Building HTML from Quarto for data620_${file_prefix}${project}..."
    quarto render "./data620_${file_prefix}${project}.qmd" --to html
}

# Function to upload to RPubs
upload_rpubs() {
    local file_prefix="${is_project:+project}"
    file_prefix="${file_prefix:-assignment}"
    # Convert to lowercase using tr command
    local title=$(echo "data620-${file_prefix}${project}" | tr '[:upper:]' '[:lower:]')
    echo "Uploading data620_${file_prefix}${project} to RPubs..."
    Rscript -e "rsconnect::rpubsUpload(\"${title}\", \"data620_${file_prefix}${project}.html\", \"data620_${file_prefix}${project}.qmd\")"
}

usage() {
    echo "Usage: $0 -p <number> [-h (build) | -r (upload to RPubs) | -a (all)] [--is-project]"
    echo "Example: ./build.sh --is-project -p 1 -h"
    echo "You must specify a number, e.g., -p 2."
    echo "Optional: Use --is-project flag to work with data620_projectX.qmd instead of data620_assignmentX.qmd"
    exit 1
}

# Parse options
project=""
is_project=""

# First, handle --is-project flag if present
for arg in "$@"; do
    case $arg in
        --is-project) is_project=1; shift ;;
    esac
done

# Ensure at least one option is passed
if [ $# -eq 0 ]; then
    usage
fi

# Then parse regular options
while getopts "p:hra" opt; do
    case $opt in
        p)
            project=$OPTARG
            ;;
        h)
            [ -z "$project" ] && usage  # Check if project is empty
            build
            ;;
        r)
            [ -z "$project" ] && usage  # Check if project is empty
            upload_rpubs
            ;;
        a)
            [ -z "$project" ] && usage  # Check if project is empty
            build
            upload_rpubs
            ;;
        \?)  # Catch invalid options
            usage
            ;;
    esac
done

# Check if the project parameter was provided
[ -z "$project" ] && usage