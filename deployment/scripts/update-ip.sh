#!/bin/bash
#
# Update Security Group Rules with Current IP Address
#
# This script updates the ALB security groups for MCP servers to allow
# access from your current public IP address. Useful when your IP changes.
#
# Usage:
#   ./update-ip.sh [OPTIONS]
#
# Options:
#   --dry-run    Show what would be changed without making changes
#   --help       Show this help message
#
# Environment variables (optional):
#   AWS_REGION   AWS region (default: us-east-1)
#   AWS_PROFILE  AWS CLI profile to use
#

set -euo pipefail

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
DRY_RUN=false

# Security group names to update
SG_NAMES=(
    "materials-supplier-mcp-sg"
    "permitting-service-mcp-sg"
    "agentcore-runtime-sg"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            head -20 "$0" | tail -18
            exit 0
            ;;
        *)
            ;;
    esac
done

# Get current public IP
log_step "Detecting Current IP Address"
MY_IP=$(curl -s https://checkip.amazonaws.com)
if [ -z "$MY_IP" ]; then
    log_error "Failed to detect public IP address"
    exit 1
fi
log_info "Your current IP: ${MY_IP}"
NEW_CIDR="${MY_IP}/32"

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN MODE - No changes will be made"
fi

# Process each security group
log_step "Updating Security Groups"

for sg_name in "${SG_NAMES[@]}"; do
    # Find security group by name
    sg_id=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=${sg_name}" \
        --query "SecurityGroups[0].GroupId" \
        --output text \
        --region "${AWS_REGION}" 2>/dev/null || echo "None")

    if [ "$sg_id" = "None" ] || [ -z "$sg_id" ] || [ "$sg_id" = "null" ]; then
        log_warn "Security group not found: ${sg_name}"
        continue
    fi

    log_info "Processing: ${sg_name} (${sg_id})"

    # Get all ingress rules as JSON
    rules_json=$(aws ec2 describe-security-groups \
        --group-ids "${sg_id}" \
        --query "SecurityGroups[0].IpPermissions" \
        --output json \
        --region "${AWS_REGION}" 2>/dev/null || echo "[]")

    # Process each rule
    rule_count=$(echo "$rules_json" | jq 'length')

    for i in $(seq 0 $((rule_count - 1))); do
        rule=$(echo "$rules_json" | jq ".[$i]")
        from_port=$(echo "$rule" | jq -r '.FromPort // "all"')
        protocol=$(echo "$rule" | jq -r '.IpProtocol')

        # Get CIDRs that end with /32
        old_cidrs=$(echo "$rule" | jq -r '.IpRanges[]? | select(.CidrIp | endswith("/32")) | .CidrIp' 2>/dev/null || echo "")

        for old_cidr in $old_cidrs; do
            [ -z "$old_cidr" ] && continue

            if [ "$old_cidr" = "$NEW_CIDR" ]; then
                log_info "  Port ${from_port}: Already using current IP (${NEW_CIDR})"
                continue
            fi

            log_info "  Port ${from_port}: ${old_cidr} -> ${NEW_CIDR}"

            if [ "$DRY_RUN" = false ]; then
                # Remove old rule
                aws ec2 revoke-security-group-ingress \
                    --group-id "${sg_id}" \
                    --protocol "${protocol}" \
                    --port "${from_port}" \
                    --cidr "${old_cidr}" \
                    --region "${AWS_REGION}" 2>/dev/null || log_warn "    Failed to remove old rule"

                # Add new rule
                aws ec2 authorize-security-group-ingress \
                    --group-id "${sg_id}" \
                    --protocol "${protocol}" \
                    --port "${from_port}" \
                    --cidr "${NEW_CIDR}" \
                    --region "${AWS_REGION}" 2>/dev/null || log_warn "    Failed to add new rule (may already exist)"
            fi
        done
    done
done

# Summary
log_step "Summary"
echo ""
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN completed. Run without --dry-run to apply changes."
else
    echo "Security groups updated to allow access from: ${MY_IP}"
fi
echo ""
echo "Security groups checked:"
for sg_name in "${SG_NAMES[@]}"; do
    echo "  - ${sg_name}"
done
echo ""
