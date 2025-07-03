#!/bin/bash

# Image Segmentation Batch Processing Script
# This script finds all JPG files in a directory or processes a single image file
# using the CLIPSeg API, then saves the masked results as PNG files and deletes the original JPG files.

set -e  # Exit on any error

# Default values
API_URL="http://localhost:8000"
TARGET_OBJECT="robot arm with the white body"
VERBOSE=false
DRY_RUN=false

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS] INPUT"
    echo ""
    echo "Process JPG files with image segmentation and save results as PNG files"
    echo ""
    echo "INPUT can be:"
    echo "  - A single image file (jpg/jpeg)"
    echo "  - A directory containing images (processes all jpg/jpeg files recursively)"
    echo ""
    echo "Note: The script will save segmented results as PNG files and delete the original JPG files."
    echo "Options:"
    echo "  -t, --target TEXT    Target object to segment (default: '$TARGET_OBJECT')"
    echo "  -u, --url URL        API server URL (default: $API_URL)"
    echo "  -v, --verbose        Enable verbose output"
    echo "  -n, --dry-run        Show what would be processed without actually doing it"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/image.jpg"
    echo "  $0 /path/to/images/"
    echo "  $0 -t 'person' -v /path/to/image.jpg"
    echo "  $0 --target 'red car' --url http://192.168.1.100:8000 /path/to/images/"
    echo "  $0 --dry-run /path/to/image.jpg"
    echo ""
}

# Function to log messages
log() {
    if [ "$VERBOSE" = true ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    fi
}

# Function to log errors
log_error() {
    echo "[ERROR] $1" >&2
}

# Function to log info
log_info() {
    echo "[INFO] $1"
}

# Function to check if API is available
check_api() {
    log "Checking API availability at $API_URL"
    if curl -s --max-time 10 "$API_URL/" > /dev/null 2>&1; then
        log "API is available"
        return 0
    else
        log_error "API is not available at $API_URL"
        log_error "Please ensure the image segmentation server is running"
        return 1
    fi
}

# Function to check if file is a valid image file
is_image_file() {
    local file_path="$1"
    local filename=$(basename "$file_path")
    local extension="${filename##*.}"
    
    # Check if extension is jpg or jpeg (case insensitive)
    if [[ "${extension,,}" == "jpg" ]] || [[ "${extension,,}" == "jpeg" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to process a single image
process_image() {
    local image_path="$1"
    local image_name=$(basename "$image_path")
    local image_name_no_ext="${image_name%.*}"
    local image_dir=$(dirname "$image_path")
    local output_path="${image_dir}/${image_name_no_ext}.png"
    local temp_output="/tmp/segmented_${image_name_no_ext}_$$.png"
    
    log "Processing: $image_path"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would process $image_path with target '$TARGET_OBJECT'"
        log_info "DRY RUN: Would save PNG result to $output_path and delete original JPG"
        return 0
    fi
    
    # Make API request
    if curl -s --max-time 60 \
        -X POST \
        -F "image=@$image_path" \
        -F "target=$TARGET_OBJECT" \
        "$API_URL/segment" \
        -o "$temp_output"; then
        
        # Check if we got a valid response (non-empty file)
        if [ -s "$temp_output" ]; then
            # Move the PNG result to the final location
            if mv "$temp_output" "$output_path"; then
                # Delete the original JPG file
                if rm "$image_path"; then
                    log_info "Successfully processed: $image_path -> $output_path"
                    return 0
                else
                    log_error "Failed to delete original file: $image_path"
                    return 1
                fi
            else
                log_error "Failed to save PNG result: $output_path"
                rm -f "$temp_output"
                return 1
            fi
        else
            log_error "API returned empty response for: $image_path"
            rm -f "$temp_output"
            return 1
        fi
    else
        log_error "Failed to process: $image_path"
        rm -f "$temp_output"
        return 1
    fi
}

# Function to find and process all JPG files
process_directory() {
    local directory="$1"
    local total_files=0
    local processed_files=0
    local failed_files=0
    
    log_info "Searching for JPG files in: $directory"
    
    # Find all JPG files (case insensitive)
    while IFS= read -r -d '' image_path; do
        total_files=$((total_files + 1))
        
        if process_image "$image_path"; then
            processed_files=$((processed_files + 1))
        else
            failed_files=$((failed_files + 1))
        fi
        
        # Progress indicator
        if [ "$VERBOSE" = true ]; then
            echo -ne "\rProgress: $processed_files/$total_files processed, $failed_files failed"
        fi
        
    done < <(find "$directory" -type f \( -iname "*.jpg" -o -iname "*.jpeg" \) -print0)
    
    echo  # New line after progress indicator
    
    log_info "Processing complete:"
    log_info "  Total files found: $total_files"
    log_info "  Successfully processed: $processed_files"
    log_info "  Failed: $failed_files"
    
    return 0
}

# Function to process a single image file
process_single_file() {
    local file_path="$1"
    
    log_info "Processing single file: $file_path"
    
    if process_image "$file_path"; then
        log_info "Successfully processed: $file_path"
        return 0
    else
        log_error "Failed to process: $file_path"
        return 1
    fi
}

# Function to determine input type and process accordingly
process_input() {
    local input_path="$1"
    
    if [ -f "$input_path" ]; then
        # It's a file
        if is_image_file "$input_path"; then
            process_single_file "$input_path"
        else
            log_error "File is not a valid image file (jpg/jpeg): $input_path"
            return 1
        fi
    elif [ -d "$input_path" ]; then
        # It's a directory
        process_directory "$input_path"
    else
        log_error "Input path does not exist: $input_path"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET_OBJECT="$2"
            shift 2
            ;;
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            INPUT_PATH="$1"
            shift
            ;;
    esac
done

# Check if input path is provided
if [ -z "$INPUT_PATH" ]; then
    log_error "Input path is required"
    usage
    exit 1
fi

# Check if input path exists
if [ ! -e "$INPUT_PATH" ]; then
    log_error "Input path does not exist: $INPUT_PATH"
    exit 1
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    log_error "Please install curl: apt-get install curl"
    exit 1
fi

# Display configuration
log_info "Configuration:"
log_info "  Input path: $INPUT_PATH"
log_info "  Target object: $TARGET_OBJECT"
log_info "  API URL: $API_URL"
log_info "  Verbose: $VERBOSE"
log_info "  Dry run: $DRY_RUN"

# Check API availability (skip for dry run)
if [ "$DRY_RUN" = false ]; then
    if ! check_api; then
        exit 1
    fi
fi

# Process the input
log_info "Starting processing..."
process_input "$INPUT_PATH"

log_info "Processing completed!"
