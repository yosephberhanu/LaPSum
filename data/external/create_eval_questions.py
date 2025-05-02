import sqlite3
import os
import csv

# Maps placeholders to database tables and their respective columns
placeholder_table_map = {
    'CLASS': ('class_models', 'class_name'),
    'METHOD': ('method_models', 'method_name'),
    'PACKAGE': ('code_models', 'namespace'),
    'PROJECT': ('code_models', 'filepath'),
    'FILES': ('code_models', 'filepath')  # We no longer use this for PROJECT
}


def get_random_entity(conn, entity_type):
    """Fetch a random value from the database based on entity type."""
    table, column = placeholder_table_map.get(entity_type, (None, None))
    if not table or not column:
        return f"Unknown{entity_type}"

    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT {column} FROM {table} ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return f"Sample{entity_type}"
        value = row[0]
        if entity_type == "FILES":
            return os.path.basename(value)  # Extract only the filename
        return value
    except sqlite3.OperationalError:
        return f"Sample{entity_type}"

def get_multiple_unique_entities(conn, entity_type, count):
    """Fetch a list of unique values for an entity type."""
    table, column = placeholder_table_map.get(entity_type, (None, None))
    if not table or not column:
        return [f"Sample{entity_type}{i+1}" for i in range(count)]

    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT DISTINCT {column} FROM {table} ORDER BY RANDOM() LIMIT {count}")
        rows = cursor.fetchall()
        values = [os.path.basename(row[0]) if entity_type == "FILES" else row[0] for row in rows]
        while len(values) < count:
            values.append(f"Sample{entity_type}{len(values)+1}")
        return values
    except sqlite3.OperationalError:
        return [f"Sample{entity_type}{i+1}" for i in range(count)]


def fill_placeholders(template, conn, project_name):
    """Replace placeholders like {CLASS}, {METHOD}, {PROJECT} with actual values."""
    result = template
    cursor = conn.cursor()

    if template.count("{METHOD}") == 2:
        # Special case: get a class with at least 2 methods
        cursor.execute("""
            SELECT cm.id, cm.class_name
            FROM class_models cm
            JOIN method_models mm ON cm.id = mm.class_model_id
            GROUP BY cm.id
            HAVING COUNT(mm.id) >= 2
            ORDER BY RANDOM()
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            class_id, class_name = row
        else:
            class_name = "SampleClass"
            method_names = ["SampleMethod1", "SampleMethod2"]
            result = result.replace("{METHOD}", method_names[0], 1)
            result = result.replace("{METHOD}", method_names[1], 1)
            return result.replace("{CLASS}", class_name)

        # Get two methods from that class
        cursor.execute("""
            SELECT method_name 
            FROM method_models 
            WHERE class_model_id = ?
            ORDER BY RANDOM() 
            LIMIT 2
        """, (class_id,))
        method_rows = cursor.fetchall()
        method_names = [row[0] for row in method_rows]

        result = result.replace("{METHOD}", method_names[0], 1)
        result = result.replace("{METHOD}", method_names[1], 1)
        return result.replace("{CLASS}", class_name)

    # Normal case: handle one placeholder per type
    for placeholder in placeholder_table_map:
        token = f"{{{placeholder}}}"
        count = template.count(token)
        if count == 1:
            # Single replacement
            if placeholder == 'PROJECT':
                replacement = project_name
            else:
                replacement = get_random_entity(conn, placeholder)
            result = result.replace(token, replacement.replace(";", ""))
        elif count >= 2:
            # Two or more replacements: get distinct values
            values = get_multiple_unique_entities(conn, placeholder, count)
            for val in values:
                result = result.replace(token, val.replace(";", ""), 1)
    return result


def generate_rows(project_name, db_path, templates, start_id=1):
    """Generate filled questions for a single project."""
    conn = sqlite3.connect(db_path)
    rows = []
    row_id = start_id

    for question_id, template in enumerate(templates, start=1):
        filled = fill_placeholders(template, conn, project_name)
        row = {
            "id": row_id,
            "project": project_name,
            "question_id": question_id,
            "customized_quesstion": filled
        }
        rows.append(row)
        row_id += 1

    conn.close()
    return rows, row_id


# === Load question templates from text file ===
with open("questions.txt", "r", encoding="utf-8") as f:
    question_templates = [line.strip() for line in f if line.strip()]

# === Project to SQLite database mapping ===
projects = {
    "wg/scrypt": "D:\\Projects\\mimir\\output\\wg_scrypt\\code_data.db",
    "groovy/groovy-core": "D:\\Projects\\mimir\\output\\groovy_groovy-core\\code_data.db",
    "joestelmach/natty": "D:\\Projects\\mimir\\output\\joestelmach_natty\\code_data.db",
    "sstrickx/yahoofinance-api": "D:\\Projects\\mimir\\output\\sstrickx_yahoofinance-api\\code_data.db",
    "pedrovgs/Renderers": "D:\\Projects\\mimir\\output\\pedrovgs_Renderers\\code_data.db"
}

# === Generate all rows for CSV ===
all_rows = []
next_id = 1
for project_name, db_path in projects.items():
    rows, next_id = generate_rows(project_name, db_path, question_templates, start_id=next_id)
    all_rows.extend(rows)

# === Write to final CSV ===
with open("filled_questions_v2.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "project", "question_id", "customized_quesstion"])
    writer.writeheader()
    writer.writerows(all_rows)

print("✅ CSV file 'filled_questions_v2.csv' has been generated.")