from enum import StrEnum


class Buttons(StrEnum):
    OWNER = "🌚 Owner"
    BACK = "🔙 Back"
    YES = "✅ Yes"
    NO = "❌ No"

    ### Clients
    CLIENTS_ADD = "➕ Add Client"
    CLIENTS_CHANGE_SECRET = "🔑 Change Secret"
    CLIENTS_CHANGE_REMARK = "✏️ Change Remark"
    CLIENTS_REMOVE = "❌ Remove Client"
    CLIENTS_SETTING = "⚙️ Client Settings"
    CLIENTS_CREATE = "🆕 Create Client"

    ### Servers
    SERVERS = "🖥️ Servers"
    SERVERS_REBOOT = "🔄 Reboot"
    SERVERS_REBUILD = "🛠️ Rebuild"
    SERVERS_POWER_ON = "⚡ Power On"
    SERVERS_POWER_OFF = "🔌 Power Off"
    SERVERS_RESET_PASSWORD = "🔓 Reset Password"
    SERVERS_RESET = "🔄 Reset"
    SERVERS_REMOVE = "🗑️ Remove Server"
    SERVERS_CREATE = "➕ Create Server"
    SERVERS_CREATE_SNAPSHOT = "📷 Create Snapshot"
    SERVERS_DEL_SNAPSHOT = "🗑️ Delete Snapshot"
    SERVERS_REMARK = "✏️ Change Remark"
    SERVERS_ASSIGN_IPV4 = "🔗 Assign IPv4"
    SERVERS_ASSIGN_IPV6 = "🔗 Assign IPv6"
    SERVERS_UNASSIGN_IPV4 = "❌ Unassign IPv4"
    SERVERS_UNASSIGN_IPV6 = "❌ Unassign IPv6"
    SERVERS_UPGRADE = "⬆️ Upgrade"
    SERVERS_REFRESH = "🔄 Refresh"
    SERVERS_ACCESS_GRANT = "➕ Grant Access"
    SERVERS_ACCESS_LIST = "📋 List Access"
    SERVERS_ACCESS_REVOKE = "❌ Revoke Access"

    ### Snapshots
    SNAPSHOTS = "📸 Snapshots"
    SNAPSHOTS_CREATE = "➕ Create Snapshot"
    SNAPSHOTS_RESTORE = "🔄 Restore Snapshot"
    SNAPSHOTS_DELETE = "🗑️ Delete Snapshot"
    SNAPSHOTS_REMARK = "✏️ Change Remark"

    ### Primary IPs
    PRIMARY_IPS = "🌐 Primary IPs"
    PRIMARY_IPS_CREATE = "➕ Create Primary IP"
    PRIMARY_IPS_ASSIGN = "🔗 Assign IP"
    PRIMARY_IPS_UNASSIGN = "❌ Unassign IP"
    PRIMARY_IPS_REMARK = "✏️ Change Remark"
    PRIMARY_IPS_DELETE = "🗑️ Delete IP"
    PRIMARY_IPS_CREATE_IPV4 = "➕ Create IPv4"
    PRIMARY_IPS_CREATE_IPV6 = "➕ Create IPv6"

    ### Volumes
    VOLUMES = "💾 Volumes"
    VOLUMES_CREATE = "➕ Create Volume"
    VOLUMES_REMARK = "✏️ Change Remark"
    VOLUMES_DELETE = "🗑️ Delete Volume"
    VOLUMES_RESIZE = "⬆️ Resize Volume"
    VOLUMES_ATTACH = "🔗 Attach to Server"
    VOLUMES_DETACH = "❌ Detach from Server"

    ### Floating IPs
    FLOATING_IPS = "🔗 Floating IPs"
    FLOATING_IPS_CREATE = "➕ Create Floating IP"
    FLOATING_IPS_CREATE_IPV4 = "➕ Create IPv4"
    FLOATING_IPS_CREATE_IPV6 = "➕ Create IPv6"
    FLOATING_IPS_REMARK = "✏️ Change Remark"
    FLOATING_IPS_DELETE = "🗑️ Delete Floating IP"
    FLOATING_IPS_ASSIGN = "🔗 Assign to Server"
    FLOATING_IPS_UNASSIGN = "❌ Unassign from Server"
    FLOATING_IPS_CHANGE_DNS = "🌍 Change DNS"

    ### Networks
    NETWORKS = "🕸️ Networks"
    NETWORKS_CREATE = "➕ Create Network"
    NETWORKS_REMARK = "✏️ Change Remark"
    NETWORKS_DELETE = "🗑️ Delete Network"
    NETWORKS_ADD_SUBNET = "➕ Add Subnet"
    NETWORKS_DEL_SUBNET = "❌ Delete Subnet"
    NETWORKS_ADD_ROUTE = "➕ Add Route"
    NETWORKS_DEL_ROUTE = "❌ Delete Route"

    ### Firewalls
    FIREWALLS = "🛡️ Firewalls"
    FIREWALLS_CREATE = "➕ Create Firewall"
    FIREWALLS_REMARK = "✏️ Change Remark"
    FIREWALLS_DELETE = "🗑️ Delete Firewall"
    FIREWALLS_APPLY = "🔗 Apply to Servers"
    FIREWALLS_REMOVE = "❌ Remove from Servers"

    ### Load Balancers
    LOAD_BALANCERS = "⚖️ Load Balancers"
    LOAD_BALANCERS_CREATE = "➕ Create Load Balancer"
    LOAD_BALANCERS_REMARK = "✏️ Change Remark"
    LOAD_BALANCERS_DELETE = "🗑️ Delete Load Balancer"
    LOAD_BALANCERS_ADD_TARGET = "🔗 Add Target"
    LOAD_BALANCERS_DEL_TARGET = "❌ Remove Target"

    ### SSH Keys
    SSH_KEYS = "🔐 SSH Keys"
    SSH_KEYS_CREATE = "➕ Add SSH Key"
    SSH_KEYS_REMARK = "✏️ Change Remark"
    SSH_KEYS_DELETE = "🗑️ Delete SSH Key"

    ### Certificates
    CERTIFICATES = "📜 Certificates"
    CERTIFICATES_CREATE = "➕ Add Certificate"
    CERTIFICATES_CREATE_MANAGED = "🌍 Create Managed Cert"
    CERTIFICATES_REMARK = "✏️ Change Remark"
    CERTIFICATES_DELETE = "🗑️ Delete Certificate"

    ### Placement Groups
    PLACEMENT_GROUPS = "📍 Placement Groups"
    PLACEMENT_GROUPS_CREATE = "➕ Create Placement Group"
    PLACEMENT_GROUPS_REMARK = "✏️ Change Remark"
    PLACEMENT_GROUPS_DELETE = "🗑️ Delete Placement Group"
