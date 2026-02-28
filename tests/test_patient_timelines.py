import pytest
from bhv.db import (
    init_db,
    create_disease_template,
    create_disease_stage,
    clone_disease_template,
    get_stages_for_template,
    get_disease_templates
)
import tempfile
import os
import json

@pytest.fixture
def mock_db():
    import bhv.db
    # Truncate all tables to ensure clean state
    if hasattr(bhv.db, 'tdb'):
        bhv.db.users.truncate()
        bhv.db.entries.truncate()
        bhv.db.templates.truncate()
        bhv.db.stages.truncate()
        bhv.db.journeys.truncate()
    elif hasattr(bhv.db, 'db'):
        # For mongodb
        bhv.db.db.users.delete_many({})
        bhv.db.db.entries.delete_many({})
        bhv.db.db.templates.delete_many({})
        bhv.db.db.stages.delete_many({})
        bhv.db.db.journeys.delete_many({})
        
    yield

def test_patient_timeline_cloning(mock_db):
    """
    Ensures that when a patient selects a template, it does a deep clone 
    of the template and all child stages, preserving the original Admin 
    template unharmed.
    """
    
    # 1. Admin creates a baseline global template
    admin_template_id = create_disease_template(
        name="Global Anxiety Protocol", 
        description="Standard baseline", 
        created_by="admin"
    )
    
    # Admin adds some stages
    create_disease_stage(admin_template_id, "Assessment", 1, "Initial eval")
    create_disease_stage(admin_template_id, "CBT Level 1", 2, "Cognitive therapy")
    
    # 2. Verify global template exists
    globals = get_disease_templates(created_by="admin")
    assert len(globals) == 1
    assert globals[0]['name'] == "Global Anxiety Protocol"
    
    # 3. Patient clones the template 
    patient_email = "patient@test.com"
    cloned_id = clone_disease_template(admin_template_id, patient_email)
    
    # 4. Verify the clone exists and belongs uniquely to the patient
    assert cloned_id is not None
    assert cloned_id != admin_template_id
    
    patient_templates = get_disease_templates(created_by=patient_email)
    assert len(patient_templates) == 1
    assert patient_templates[0]['name'] == "Global Anxiety Protocol"
    
    # 5. Verify the stages were deep cloned cleanly
    admin_stages = get_stages_for_template(admin_template_id)
    patient_stages = get_stages_for_template(cloned_id)
    
    assert len(admin_stages) == 2
    assert len(patient_stages) == 2
    
    # Ensure they are distinct records with the same internal data but different parent template mappings
    assert str(patient_stages[0]['template_id']) == str(cloned_id)
    assert patient_stages[0]['name'] == "Assessment"
    
    assert str(patient_stages[1]['template_id']) == str(cloned_id)
    assert patient_stages[1]['name'] == "CBT Level 1"
    
    # 6. Mutating the clone should NOT change the parent
    create_disease_stage(cloned_id, "Patient Custom Stage", 3, "Only visible to patient")
    
    assert len(get_stages_for_template(admin_template_id)) == 2
    assert len(get_stages_for_template(cloned_id)) == 3
