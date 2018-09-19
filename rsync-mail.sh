#!/bin/bash
rsync -av --usermap=:simson --exclude '.imap/' /home/*/Mail /home/*/*/Mail /var/mail/ /var/lib/mysql/ /storage/shared/backup-kim
