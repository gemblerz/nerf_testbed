#!/bin/bash

# DHCP Server Setup Script for Ubuntu
# This script configures or removes a dnsmasq-based DHCP/DNS server on a specified Ethernet interface
# and enables/disables internet sharing from the host to the private network
# Uses NetworkManager (nmcli) for network interface configuration and dnsmasq for DHCP/DNS services

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage information
show_usage() {
    echo "Usage: $0 <install|uninstall> <ethernet_interface>"
    echo ""
    echo "Commands:"
    echo "  install    - Set up DHCP server on the specified interface"
    echo "  uninstall  - Remove DHCP server configuration and restore original settings"
    echo ""
    echo "Example:"
    echo "  $0 install eth0     - Install DHCP server on eth0"
    echo "  $0 uninstall eth0   - Uninstall DHCP server from eth0"
    echo ""
    echo "Available interfaces:"
    ip link show | grep -E "^[0-9]+" | awk -F': ' '{print "  " $2}' | grep -v lo
}

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if parameters are provided
if [ $# -ne 2 ]; then
    print_error "Invalid number of arguments"
    show_usage
    exit 1
fi

ACTION=$1
INTERFACE=$2

# Validate action parameter
if [[ "$ACTION" != "install" && "$ACTION" != "uninstall" ]]; then
    print_error "Invalid action: $ACTION"
    show_usage
    exit 1
fi

# Network configuration variables
DHCP_RANGE_START="10.31.81.10"
DHCP_RANGE_END="10.31.81.100"
SUBNET="10.31.81.0"
NETMASK="255.255.255.0"
STATIC_IP="10.31.81.1"
BROADCAST="10.31.81.255"

# Check if interface exists
if ! ip link show "$INTERFACE" >/dev/null 2>&1; then
    print_error "Interface $INTERFACE does not exist"
    show_usage
    exit 1
fi

# Function to install DHCP server
install_dhcp_server() {
    print_info "Installing DHCP server on interface: $INTERFACE"

    # Check if NetworkManager is installed and running
    print_info "Checking NetworkManager status..."
    if ! command -v nmcli >/dev/null 2>&1; then
        print_info "NetworkManager not found. Installing NetworkManager..."
        apt update
        apt install -y network-manager
    fi

    if ! systemctl is-active --quiet NetworkManager; then
        print_info "Starting NetworkManager service..."
        systemctl start NetworkManager
        systemctl enable NetworkManager
    fi

    # Update package list
    print_info "Updating package list..."
    apt update

    # Install dnsmasq for DHCP and DNS services
    print_info "Installing dnsmasq..."
    apt install -y dnsmasq

    # Backup original configuration files
    print_info "Backing up original configuration files..."
    if [ -f /etc/dnsmasq.conf ]; then
        cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup.$(date +%Y%m%d_%H%M%S)
    fi

    # Store original NetworkManager connection configuration for restoration
    print_info "Storing original NetworkManager connection configuration..."
    mkdir -p /etc/dhcp-server-backup
    
    # Get current connection name for the interface
    ORIGINAL_CONNECTION=$(nmcli -t -f NAME,DEVICE connection show --active | grep ":$INTERFACE$" | cut -d: -f1)
    if [ -n "$ORIGINAL_CONNECTION" ]; then
        echo "ORIGINAL_CONNECTION=$ORIGINAL_CONNECTION" > /etc/dhcp-server-backup/dhcp-config.env
        print_info "Found existing connection: $ORIGINAL_CONNECTION"
    else
        echo "ORIGINAL_CONNECTION=" > /etc/dhcp-server-backup/dhcp-config.env
        print_info "No active connection found for interface $INTERFACE"
    fi
    
    echo "INTERFACE=$INTERFACE" >> /etc/dhcp-server-backup/dhcp-config.env

    # Configure the network interface with static IP using NetworkManager
    print_info "Configuring static IP for interface $INTERFACE using NetworkManager..."

    # Delete any existing connection for this interface
    if [ -n "$ORIGINAL_CONNECTION" ]; then
        print_info "Temporarily disconnecting existing connection: $ORIGINAL_CONNECTION"
        nmcli connection down "$ORIGINAL_CONNECTION" 2>/dev/null || true
    fi

    # Create new connection with static IP
    print_info "Creating new static IP connection for $INTERFACE..."
    nmcli connection add \
        type ethernet \
        con-name "dhcp-server-$INTERFACE" \
        ifname "$INTERFACE" \
        ip4 "$STATIC_IP/24" \
        gw4 "" \
        ipv4.dns "8.8.8.8,8.8.4.4" \
        ipv4.method manual \
        autoconnect yes

    # Activate the new connection
    print_info "Activating new connection..."
    nmcli connection up "dhcp-server-$INTERFACE"

    # Wait for interface to come up
    sleep 3

    # Configure dnsmasq for DHCP and DNS services
    print_info "Configuring dnsmasq for DHCP and DNS services..."
    
    # Extract search domains from host's resolv.conf
    SEARCH_DOMAINS=$(grep -E "^search " /etc/resolv.conf | head -1 | sed 's/^search //' | tr ' ' ',')
    if [ -z "$SEARCH_DOMAINS" ]; then
        # Fallback to domain directive if no search directive
        SEARCH_DOMAINS=$(grep -E "^domain " /etc/resolv.conf | head -1 | sed 's/^domain //')
    fi
    
    if [ -n "$SEARCH_DOMAINS" ]; then
        print_info "Found search domains: $SEARCH_DOMAINS"
    else
        print_warning "No search domains found in /etc/resolv.conf"
        SEARCH_DOMAINS="local"
    fi
    
    cat > /etc/dnsmasq.d/dhcp-server.conf << EOF
# DHCP and DNS Server Configuration
# Generated by setup-dhcp.sh

# Listen only on the specified interface
interface=$INTERFACE
bind-interfaces

# DHCP configuration - infinite lease time
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,infinite
dhcp-option=option:router,$STATIC_IP
dhcp-option=option:dns-server,$STATIC_IP
dhcp-option=option:domain-search,$SEARCH_DOMAINS

# DNS configuration
# Don't read /etc/hosts
no-hosts

# Use host's /etc/resolv.conf for upstream DNS servers
# (no-resolv option removed to allow reading /etc/resolv.conf)

# Cache DNS queries
cache-size=1000

# Enable DHCP logging
log-dhcp

# Domain name for DHCP clients
domain=local

EOF

    # Create NetworkManager connection file
    print_info "Creating NetworkManager connection file..."
    cat > "/etc/NetworkManager/system-connections/local-$INTERFACE.nmconnection" << EOF
[connection]
id=local-$INTERFACE
type=ethernet
autoconnect=true
interface-name=$INTERFACE
permissions=

[ethernet]
auto-negotiate=true
mac-address-blacklist=

[ipv4]
address1=$STATIC_IP/24
dns-search=
method=manual
never-default=true

[ipv6]
addr-gen-mode=stable-privacy
dns-search=
method=ignore
EOF

    # Set correct permissions for the connection file
    chmod 600 "/etc/NetworkManager/system-connections/local-$INTERFACE.nmconnection"
    chown root:root "/etc/NetworkManager/system-connections/local-$INTERFACE.nmconnection"

    # Reload NetworkManager to recognize the new connection file
    print_info "Reloading NetworkManager configuration..."
    nmcli connection reload

    # Backup original sysctl.conf
    if [ ! -f /etc/dhcp-server-backup/sysctl.conf.backup ]; then
        cp /etc/sysctl.conf /etc/dhcp-server-backup/sysctl.conf.backup
    fi

    # Enable IP forwarding
    print_info "Enabling IP forwarding..."
    if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
        echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
    fi
    sysctl -p

    # Find the internet-connected interface (usually the default route interface)
    INTERNET_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
    print_info "Detected internet interface: $INTERNET_INTERFACE"

    # Store internet interface for uninstall
    echo "INTERNET_INTERFACE=$INTERNET_INTERFACE" >> /etc/dhcp-server-backup/dhcp-config.env

    # Backup current iptables rules
    print_info "Backing up current iptables rules..."
    iptables-save > /etc/dhcp-server-backup/iptables-original.rules

    # Configure iptables for NAT (Network Address Translation)
    print_info "Configuring iptables for internet sharing..."

    # Enable NAT
    iptables -t nat -A POSTROUTING -o $INTERNET_INTERFACE -j MASQUERADE
    iptables -A FORWARD -i $INTERNET_INTERFACE -o $INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i $INTERFACE -o $INTERNET_INTERFACE -j ACCEPT

    # Save iptables rules
    print_info "Saving iptables rules..."
    apt install -y iptables-persistent
    netfilter-persistent save

    # Update the systemd service dependency
    cat > /etc/systemd/system/dhcp-iptables.service << EOF
[Unit]
Description=Restore iptables rules for DHCP server
Before=dnsmasq.service
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

    # Enable the iptables service
    systemctl enable dhcp-iptables.service

    # Activate the NetworkManager connection
    print_info "Activating NetworkManager connection..."
    nmcli connection up "local-$INTERFACE"

    # Start and enable dnsmasq
    print_info "Starting and enabling dnsmasq..."
    systemctl restart dnsmasq
    systemctl enable dnsmasq

    # Check service status
    if systemctl is-active --quiet dnsmasq; then
        print_info "dnsmasq (DHCP/DNS server) is running successfully!"
    else
        print_error "dnsmasq failed to start. Checking logs..."
        journalctl -u dnsmasq --no-pager -n 20
        exit 1
    fi

    # Display configuration summary
    print_info "DHCP Server Installation Complete!"
    echo "=================================================="
    echo "Interface: $INTERFACE"
    echo "Server IP: $STATIC_IP"
    echo "DHCP Range: $DHCP_RANGE_START - $DHCP_RANGE_END"
    echo "Subnet: $SUBNET/$NETMASK"
    echo "Internet Interface: $INTERNET_INTERFACE"
    echo "=================================================="
    print_info "Clients connecting to $INTERFACE will receive IP addresses in the range $DHCP_RANGE_START - $DHCP_RANGE_END"
    print_info "Internet access is enabled through $INTERNET_INTERFACE"

    # Show service status
    print_info "Service status:"
    systemctl status dnsmasq --no-pager -l

    print_info "Installation completed successfully!"
    print_warning "Note: Make sure to connect devices to the $INTERFACE interface to receive DHCP addresses"
    print_info "To uninstall, run: $0 uninstall $INTERFACE"
}

# Function to uninstall DHCP server
uninstall_dhcp_server() {
    print_info "Uninstalling DHCP server from interface: $INTERFACE"

    # Check if backup configuration exists
    if [ ! -f /etc/dhcp-server-backup/dhcp-config.env ]; then
        print_warning "No backup configuration found. This may not have been installed with this script."
        print_info "Proceeding with basic cleanup..."
    else
        # Load stored configuration
        source /etc/dhcp-server-backup/dhcp-config.env
        print_info "Found backup configuration for interface: $INTERFACE"
    fi

    # Stop and disable dnsmasq
    print_info "Stopping and disabling dnsmasq..."
    systemctl stop dnsmasq 2>/dev/null || true
    systemctl disable dnsmasq 2>/dev/null || true

    # Remove dnsmasq configuration
    print_info "Removing dnsmasq configuration..."
    rm -f /etc/dnsmasq.d/dhcp-server.conf

    # Restore original dnsmasq configuration if it exists
    DNSMASQ_BACKUP=$(ls -t /etc/dnsmasq.conf.backup.* 2>/dev/null | head -1)
    if [ -n "$DNSMASQ_BACKUP" ]; then
        cp "$DNSMASQ_BACKUP" /etc/dnsmasq.conf
        print_info "Restored dnsmasq configuration from $DNSMASQ_BACKUP"
        # Restart dnsmasq with original configuration if it's not empty
        if [ -s /etc/dnsmasq.conf ]; then
            systemctl restart dnsmasq
            systemctl enable dnsmasq
            print_info "Restarted dnsmasq with original configuration"
        fi
    fi

    # Stop and disable iptables service
    print_info "Stopping and disabling iptables service..."
    systemctl stop dhcp-iptables.service 2>/dev/null || true
    systemctl disable dhcp-iptables.service 2>/dev/null || true

    # Remove systemd service file
    print_info "Removing systemd service file..."
    rm -f /etc/systemd/system/dhcp-iptables.service
    systemctl daemon-reload

    # Restore original iptables rules
    print_info "Restoring original iptables rules..."
    if [ -f /etc/dhcp-server-backup/iptables-original.rules ]; then
        iptables-restore < /etc/dhcp-server-backup/iptables-original.rules
        netfilter-persistent save
        print_info "Original iptables rules restored"
    else
        print_warning "No original iptables backup found. Flushing all rules..."
        iptables -F
        iptables -t nat -F
        iptables -t mangle -F
        iptables -X
        iptables -P INPUT ACCEPT
        iptables -P FORWARD ACCEPT
        iptables -P OUTPUT ACCEPT
        netfilter-persistent save
    fi

    # Restore original sysctl configuration
    print_info "Restoring original sysctl configuration..."
    if [ -f /etc/dhcp-server-backup/sysctl.conf.backup ]; then
        cp /etc/dhcp-server-backup/sysctl.conf.backup /etc/sysctl.conf
        sysctl -p
        print_info "Original sysctl configuration restored"
    else
        print_warning "No sysctl backup found. Disabling IP forwarding..."
        sed -i '/^net.ipv4.ip_forward=1$/d' /etc/sysctl.conf
        echo 'net.ipv4.ip_forward=0' >> /etc/sysctl.conf
        sysctl -p
    fi

    # Remove NetworkManager connection
    print_info "Removing NetworkManager connection..."
    nmcli connection down "local-$INTERFACE" 2>/dev/null || true
    nmcli connection delete "local-$INTERFACE" 2>/dev/null || true
    
    # Also remove the direct connection file if it exists
    if [ -f "/etc/NetworkManager/system-connections/local-$INTERFACE.nmconnection" ]; then
        rm -f "/etc/NetworkManager/system-connections/local-$INTERFACE.nmconnection"
        print_info "Removed NetworkManager connection file for $INTERFACE"
    fi
    
    # Reload NetworkManager to recognize the changes
    nmcli connection reload

    # Restore original connection if it existed
    if [ -n "$ORIGINAL_CONNECTION" ] && [ "$ORIGINAL_CONNECTION" != "" ]; then
        print_info "Restoring original connection: $ORIGINAL_CONNECTION"
        nmcli connection up "$ORIGINAL_CONNECTION" 2>/dev/null || true
    else
        print_info "Creating new DHCP connection for interface $INTERFACE..."
        # Create a new DHCP connection
        nmcli connection add \
            type ethernet \
            con-name "restored-$INTERFACE" \
            ifname "$INTERFACE" \
            ipv4.method auto \
            autoconnect yes
        nmcli connection up "restored-$INTERFACE"
    fi

    # Wait for interface to come up
    sleep 3

    # Optionally remove dnsmasq package
    read -p "Do you want to remove the dnsmasq package? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing dnsmasq package..."
        apt remove -y dnsmasq
        apt autoremove -y
    else
        print_info "Keeping dnsmasq package installed"
    fi

    # Clean up backup directory
    print_info "Cleaning up backup files..."
    rm -rf /etc/dhcp-server-backup

    print_info "DHCP Server Uninstallation Complete!"
    print_info "Interface $INTERFACE has been restored to its original configuration"
    print_warning "You may need to manually configure your network interface if the restore didn't work as expected"
    print_info "Uninstallation completed successfully!"
}

# Main execution
case "$ACTION" in
    "install")
        install_dhcp_server
        ;;
    "uninstall")
        uninstall_dhcp_server
        ;;
    *)
        print_error "Unknown action: $ACTION"
        show_usage
        exit 1
        ;;
esac    