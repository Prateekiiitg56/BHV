import os
from datetime import datetime

MONGO_URI = os.environ.get('MONGO_URI')

if MONGO_URI:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()

    def init_db():
        # Ensure indexes
        db.users.create_index('email', unique=True)
        db.entries.create_index('patient_id')

    def create_user(email, password_hash, role='patient'):
        user = {'email': email, 'password': password_hash, 'role': role}
        res = db.users.insert_one(user)
        return str(res.inserted_id)

    def get_user_by_email(email):
        return db.users.find_one({'email': email})

    def create_entry(patient_id, filename, narrative, timestamp=None, stage_id=None, journey_id=None):
        doc = {'patient_id': patient_id, 'filename': filename, 'narrative': narrative, 'timestamp': timestamp or datetime.utcnow()}
        if stage_id: doc['stage_id'] = stage_id
        if journey_id: doc['journey_id'] = journey_id
        res = db.entries.insert_one(doc)
        return str(res.inserted_id)

    def list_entries_for_patient(patient_id):
        return list(db.entries.find({'patient_id': patient_id}))

    def list_all_entries():
        return list(db.entries.find())

    def get_entry(entry_id):
        from bson import ObjectId
        return db.entries.find_one({'_id': ObjectId(entry_id)})

    def delete_entry(entry_id):
        from bson import ObjectId
        db.entries.delete_one({'_id': ObjectId(entry_id)})

    def update_entry(entry_id, **kwargs):
        from bson import ObjectId
        db.entries.update_one({'_id': ObjectId(entry_id)}, {'$set': kwargs})

    # Timeline / Journey Additions
    def create_disease_template(name, description="", created_by="admin"):
        res = db.templates.insert_one({'name': name, 'description': description, 'created_by': created_by})
        return str(res.inserted_id)

    def get_disease_templates():
        return list(db.templates.find())

    def get_disease_template(template_id):
        from bson import ObjectId
        try:
            return db.templates.find_one({'_id': ObjectId(str(template_id))})
        except Exception:
            return None

    def create_disease_stage(template_id, name, order_index, description=""):
        res = db.stages.insert_one({'template_id': template_id, 'name': name, 'order_index': order_index, 'description': description})
        return str(res.inserted_id)

    def get_stages_for_template(template_id):
        return list(db.stages.find({'template_id': template_id}).sort('order_index', 1))
    

    def assign_patient_journey(patient_id, template_id, current_stage_id=None):
        doc = {
            'patient_id': patient_id,
            'template_id': template_id,
            'current_stage_id': current_stage_id,
            'started_at': datetime.utcnow(),
            'completed': False
        }
        res = db.journeys.insert_one(doc)
        return str(res.inserted_id)

    def get_patient_journeys(patient_id):
        return list(db.journeys.find({'patient_id': patient_id}))

    def update_patient_journey_stage(journey_id, new_stage_id):
        from bson import ObjectId
        db.journeys.update_one({'_id': ObjectId(journey_id)}, {'$set': {'current_stage_id': new_stage_id}})

    def complete_patient_journey(journey_id):
        from bson import ObjectId
        db.journeys.update_one({'_id': ObjectId(journey_id)}, {'$set': {'completed': True, 'completed_at': datetime.utcnow()}})

    def delete_patient_journey(journey_id, patient_id):
        from bson import ObjectId
        try:
            j = db.journeys.find_one({'_id': ObjectId(journey_id)})
            if not j or j.get('patient_id') != patient_id:
                return False
            
            template_id = j.get('template_id')
            db.journeys.delete_one({'_id': ObjectId(journey_id)})
            
            if template_id:
                other_journeys = db.journeys.find_one({'template_id': template_id})
                if not other_journeys:
                    t = db.templates.find_one({'_id': ObjectId(str(template_id))})
                    if t and t.get('created_by') == patient_id:
                        db.templates.delete_one({'_id': ObjectId(str(template_id))})
                        db.stages.delete_many({'template_id': template_id})
                        db.stages.delete_many({'template_id': str(template_id)})
                        db.stages.delete_many({'template_id': ObjectId(str(template_id))})
            return True
        except Exception:
            return False


else:
    # TinyDB fallback
    from tinydb import TinyDB, Query
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'db.json')
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    tdb = TinyDB(DB_PATH)
    users = tdb.table('users')
    entries = tdb.table('entries')
    templates = tdb.table('templates')
    stages = tdb.table('stages')
    journeys = tdb.table('journeys')
    UserQ = Query()

    def init_db():
        pass

    def create_user(email, password_hash, role='patient'):
        user = {'email': email, 'password': password_hash, 'role': role}
        return users.insert(user)

    def get_user_by_email(email):
        res = users.search(UserQ.email == email)
        return res[0] if res else None

    def create_entry(patient_id, filename, narrative, timestamp=None, stage_id=None, journey_id=None):
        doc = {'patient_id': patient_id, 'filename': filename, 'narrative': narrative, 'timestamp': (timestamp or datetime.utcnow()).isoformat()}
        if stage_id: doc['stage_id'] = stage_id
        if journey_id: doc['journey_id'] = journey_id
        return entries.insert(doc)

    def list_entries_for_patient(patient_id):
        return entries.search(Query().patient_id == patient_id)

    def list_all_entries():
        return entries.all()

    def get_entry(entry_id):
        return entries.get(doc_id=int(entry_id))

    def delete_entry(entry_id):
        entries.remove(doc_ids=[int(entry_id)])

    def update_entry(entry_id, **kwargs):
        entries.update(kwargs, doc_ids=[int(entry_id)])

    # Timeline / Journey Additions
    def create_disease_template(name, description="", created_by="admin"):
        return templates.insert({
            'name': name, 'description': description, 'created_by': created_by
        })

    def get_disease_templates(created_by=None):
        if created_by:
            return templates.search(Query().created_by == created_by)
        # Return only global Admin templates by default
        return templates.search(Query().created_by == "admin")

    def get_disease_template(template_id):
        try:
            int_id = int(template_id)
            res = templates.get(doc_id=int_id)
            if res:
                return res
        except (ValueError, TypeError):
            pass
        return None

    def create_disease_stage(template_id, name, order_index, description=""):
        return stages.insert({'template_id': template_id, 'name': name, 'order_index': int(order_index), 'description': description})

    def clone_disease_template(template_id, patient_id):
        """Deep clone an Admin template into a private patient-owned template."""
        base_template = templates.get(doc_id=int(template_id))
        if not base_template:
            return None
            
        # Create private template clone
        new_template_id = create_disease_template(
            name=base_template['name'], 
            description=base_template['description'], 
            created_by=patient_id
        )
        
        # Clone all sequence stages over to the new template
        base_stages = get_stages_for_template(template_id)
        for stage in base_stages:
            create_disease_stage(
                template_id=new_template_id,
                name=stage['name'],
                order_index=stage['order_index'],
                description=stage['description']
            )
            
        return new_template_id

    def get_stages_for_template(template_id):
        # Admin templates might be stored with integer doc_ids or string ObjectId
        # Find all stages strictly matching this template_id
        results = []
        
        # In TinyDB, custom templates assigned via doc_id are integers
        # When passed from URL, it's a string. Try exact int cast first to prevent '1' matching '11'
        try:
            int_id = int(template_id)
            results.extend(stages.search(Query().template_id == int_id))
        except (ValueError, TypeError):
            pass
            
        # Also always search for the exact string representation 
        if isinstance(template_id, str):
             results.extend(stages.search(Query().template_id == template_id))
        elif template_id is not None:
             results.extend(stages.search(Query().template_id == str(template_id)))
            
        # Deduplicate just in case 
        seen = set()
        unique_results = []
        for r in results:
            rid = r.doc_id if hasattr(r, 'doc_id') else r.get('_id')
            if rid not in seen:
                seen.add(rid)
                unique_results.append(r)
                
        return sorted(unique_results, key=lambda i: int(i.get('order_index', 0)))

    def get_stage(stage_id):
        return stages.get(doc_id=int(stage_id))

    def assign_patient_journey(patient_id, template_id, current_stage_id=None):
        doc = {
            'patient_id': patient_id,
            'template_id': template_id,  # This will now be the cloned template ID
            'current_stage_id': current_stage_id,
            'started_at': datetime.utcnow().isoformat(),
            'completed': False
        }
        return journeys.insert(doc)

    def get_patient_journeys(patient_id):
        return journeys.search(Query().patient_id == patient_id)

    def update_patient_journey_stage(journey_id, new_stage_id):
        journeys.update({'current_stage_id': new_stage_id}, doc_ids=[int(journey_id)])

    def complete_patient_journey(journey_id):
        journeys.update({'completed': True, 'completed_at': datetime.utcnow().isoformat()}, doc_ids=[int(journey_id)])

    def delete_patient_journey(journey_id, patient_id):
        """Deletes a patient journey and its associated custom template if no one else uses it."""
        j = journeys.get(doc_id=int(journey_id))
        if not j or j.get('patient_id') != patient_id:
            return False
            
        template_id = j.get('template_id')
        journeys.remove(doc_ids=[int(journey_id)])
        
        if template_id:
            other_journeys = journeys.search(Query().template_id == template_id)
            if not other_journeys:
                t = None
                try:
                    t = templates.get(doc_id=int(template_id))
                except (ValueError, TypeError):
                    pass
                if t and t.get('created_by') == patient_id:
                    templates.remove(doc_ids=[int(template_id)])
                    stages.remove(Query().template_id == int(template_id))
                    stages.remove(Query().template_id == str(template_id))
        return True

    # ── Admin-only helpers ────────────────────────────────────────────────────

    def list_all_users():
        """Return all users in the system (admin use only)."""
        all_users = users.all()
        result = []
        for u in all_users:
            user_dict = dict(u)
            user_dict['id'] = u.doc_id
            user_dict.pop('password', None)  # Never expose password hashes
            result.append(user_dict)
        return result

    def list_all_journeys():
        """Return every journey across all patients (admin use only)."""
        all_journeys = journeys.all()
        result = []
        for j in all_journeys:
            jd = dict(j)
            jd['id'] = j.doc_id
            # Attach template name
            t_id = jd.get('template_id')
            if t_id:
                try:
                    t = templates.get(doc_id=int(t_id))
                    jd['template_name'] = t.get('name', 'Unknown') if t else 'Deleted Template'
                except Exception:
                    jd['template_name'] = 'Unknown'
            else:
                jd['template_name'] = 'No Template'
            result.append(jd)
        return result

    def admin_delete_journey(journey_id):
        """Admin force-deletes any journey and its orphaned template."""
        j = journeys.get(doc_id=int(journey_id))
        if not j:
            return False
        template_id = j.get('template_id')
        journeys.remove(doc_ids=[int(journey_id)])
        if template_id:
            other_journeys = journeys.search(Query().template_id == template_id)
            if not other_journeys:
                try:
                    templates.remove(doc_ids=[int(template_id)])
                    stages.remove(Query().template_id == int(template_id))
                    stages.remove(Query().template_id == str(template_id))
                except Exception:
                    pass
        return True

    def admin_rename_journey(journey_id, new_name):
        """Admin renames a journey's underlying template."""
        j = journeys.get(doc_id=int(journey_id))
        if not j:
            return False
        template_id = j.get('template_id')
        if template_id:
            try:
                templates.update({'name': new_name}, doc_ids=[int(template_id)])
            except Exception:
                return False
        return True

    def delete_user(user_id):
        """Admin deletes a user account (does NOT delete their entries/journeys)."""
        users.remove(doc_ids=[int(user_id)])

