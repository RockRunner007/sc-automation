import gitlab
import datetime
import json
import logging
import os
import sys

def configure_logging():
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def standard_project(project):
    file_content = "Please fill out this document following the teams standard"
    
    project.files.create({'file_path': 'readme.md',
        'branch': 'main','content': file_content,
        'author_email': 'automation@gen6ventures.com',
        'author_name': 'automation',
        'commit_message': 'Create readme file'})

    project.files.create({'file_path': 'CODEOWNERS',
        'branch': 'main','content': file_content,
        'author_email': 'automation@gen6ventures.com',
        'author_name': 'automation',
        'commit_message': 'Create CODEOWNERS file'})
    
    project.branches.create({'branch': 'develop','ref': 'main'})

def project_rules(project):
    p_mras = project.approvals.get()
    p_mras.approvals_before_merge = 1
    p_mras.save()

def protect_branches(project):
    for protected_branch in project.protectedbranches.list():
        if protected_branch.name == "master":
            protected_branch.delete()
        if protected_branch.name == "main":
            protected_branch.delete()
        if protected_branch.name == "develop":
            protected_branch.delete()
    
    project.protectedbranches.create(
        {
            "name": "develop",
            "push_access_level": gitlab.MASTER_ACCESS,
            "merge_access_level": gitlab.MASTER_ACCESS,
            "allowed_to_unprotect": [
                {"access_level": gitlab.MAINTAINER_ACCESS}
            ],                
            "code_owner_approval_required" : "yes"
        }
    )
    project.protectedbranches.create(
        {
            "name": "master",
            "push_access_level": gitlab.NO_ACCESS,
            "merge_access_level": gitlab.MASTER_ACCESS,
            "allowed_to_unprotect": [
                {"access_level": gitlab.MAINTAINER_ACCESS}
            ],                
        }
    )
    project.protectedbranches.create(
        {
            "name": "main",
            "push_access_level": gitlab.NO_ACCESS,
            "merge_access_level": gitlab.MASTER_ACCESS,
            "allowed_to_unprotect": [
                {"access_level": gitlab.MAINTAINER_ACCESS}
            ],
        }
    )

def main():
    configure_logging()

    token = '{ci variables}'
    gl = gitlab.Gitlab('{ci variables}', private_token=token)

    group = gl.groups.get(314)
    projects = group.projects.list(include_subgroups=True, all=True)

    for group_project in projects:
        project = gl.projects.get(group_project.id)
        branches = project.branches.list()
        devbranch = True

        # Create branches if none exits        
        try:
            project.branches.get('develop')
        except:
            devbranch = False
            logging.info(f'{project.name} does not have a develop branch')
        
        if devbranch == False:
            if len(branches) == 0:
                standard_project(project) # Setup project if never completed

            for branch in branches:
                if branch.name == "main":
                    project.branches.create({'branch': 'develop','ref': 'main'})
                if branch.name == "master" :
                    project.branches.create({'branch': 'develop','ref': 'master'})

        protect_branches(project) # protect default branches
        project_rules(project) # assign rules to projects

if __name__ == "__main__":
    main()