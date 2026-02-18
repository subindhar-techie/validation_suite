# Constants for the validation tool

# Profile configurations
PROFILE_CONFIGS = {
    "MOB": {
        "skip_fields": [],
        "image_labels": ["INNER LABEL 500", "OUTER LABEL 5000", "ARTWORK FRONT", "ARTWORK BACK"]
    },
    "WBIOT": {
        "skip_fields": ["GLOBAL_IMSI (3031)", "GLOBAL_ACC (3037)", "HOME_ACC (3037)"],
        "image_labels": ["INNER LABEL 100", "INNER LABEL 500", "OUTER LABEL 5000", "ARTWORK FRONT", "ARTWORK BACK"]
    },
    "NBIOT": {
        "skip_fields": ["GLOBAL_IMSI (3031)", "GLOBAL_ACC (3037)", "HOME_ACC (3037)", "ASCII_IMSI (6F02)", "ASCII_IMSI (6F04)"],
        "image_labels": ["INNER LABEL 100", "INNER LABEL 500", "OUTER LABEL 5000", "ARTWORK FRONT", "ARTWORK BACK"]
    }
}

# Excel password for protection
EXCEL_PASSWORD = "Secure@123"