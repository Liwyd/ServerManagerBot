from enum import StrEnum

from eiogram.utils.callback_data import CallbackData


class AreaType(StrEnum):
    HOME = "hm"
    CLIENT = "cl"
    SNAPSHOT = "ss"
    PRIMARY_IP = "pi"
    SERVER = "sv"
    VOLUME = "vl"
    FLOATING_IP = "fi"
    NETWORK = "nw"
    FIREWALL = "fw"
    LOAD_BALANCER = "lb"
    SSH_KEY = "sk"
    CERTIFICATE = "ce"
    PLACEMENT_GROUP = "pg"


class TaskType(StrEnum):
    MENU = "mn"
    LIST = "ls"
    CREATE = "cr"
    INFO = "nf"
    UPDATE = "pt"


class StepType(StrEnum):
    CHANGE_REMARK = "cr"
    CHANGE_SECRET = "cs"
    REMOVE_CLIENT = "rmc"
    SERVERS_REBOOT = "reb"
    SERVERS_REBUILD = "rbl"
    SERVERS_POWER_ON = "pwn"
    SERVERS_POWER_OFF = "pwf"
    SERVERS_RESET_PASSWORD = "rsp"
    SERVERS_RESET = "rst"
    SERVERS_REMOVE = "rms"
    SERVERS_CREATE_SNAPSHOT = "crs"
    SERVERS_DEL_SNAPSHOT = "dsp"
    SERVERS_REMARK = "srv"
    SERVERS_UNASSIGN_IPV4 = "sua4"
    SERVERS_UNASSIGN_IPV6 = "sua6"
    SERVERS_ASSIGN_IPV4 = "saa4"
    SERVERS_ASSIGN_IPV6 = "saa6"
    SERVERS_UPGRADE = "sup"
    SERVERS_ACCESS_GRANT = "sag"
    SERVERS_ACCESS_LIST = "sal"
    SERVERS_ACCESS_REVOKE = "sar"
    SNAPSHOTS_RESTORE = "srs"
    SNAPSHOTS_DELETE = "sds"
    SNAPSHOTS_REMARK = "srm"
    PRIMARY_IPS_ASSIGN = "pia"
    PRIMARY_IPS_UNASSIGN = "pua"
    PRIMARY_IPS_REMARK = "pir"
    PRIMARY_IPS_DELETE = "pid"
    VOLUMES_REMARK = "vrm"
    VOLUMES_DELETE = "vdl"
    VOLUMES_RESIZE = "vrz"
    VOLUMES_ATTACH = "vat"
    VOLUMES_DETACH = "vdt"
    FLOATING_IPS_REMARK = "fir"
    FLOATING_IPS_DELETE = "fdl"
    FLOATING_IPS_ASSIGN = "fia"
    FLOATING_IPS_UNASSIGN = "fiu"
    FLOATING_IPS_CHANGE_DNS = "fdn"
    NETWORKS_REMARK = "nwr"
    NETWORKS_DELETE = "ndl"
    NETWORKS_ADD_SUBNET = "nas"
    NETWORKS_DEL_SUBNET = "nds"
    NETWORKS_ADD_ROUTE = "nar"
    NETWORKS_DEL_ROUTE = "ndr"
    FIREWALLS_REMARK = "fwr"
    FIREWALLS_DELETE = "fld"
    FIREWALLS_APPLY = "fwa"
    FIREWALLS_REMOVE = "fwm"
    LOAD_BALANCERS_REMARK = "lbr"
    LOAD_BALANCERS_DELETE = "lbd"
    LOAD_BALANCERS_ADD_TARGET = "lat"
    LOAD_BALANCERS_DEL_TARGET = "ldt"
    SSH_KEYS_REMARK = "skr"
    SSH_KEYS_DELETE = "skd"
    CERTIFICATES_REMARK = "cer"
    CERTIFICATES_DELETE = "ced"
    PLACEMENT_GROUPS_REMARK = "pgr"
    PLACEMENT_GROUPS_DELETE = "pgd"


class BotCB(CallbackData, prefix="x"):
    area: AreaType = AreaType.HOME
    task: TaskType = TaskType.MENU
    step: StepType | None = None
    page: int = 0
    is_approve: bool = False
    target: str | int = 0
