import boto3
import botocore
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []

    if project:
        filter = [{'Name':'tag:Name', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filter)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
def cli():
    """Shotty manages snapshots"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None, help="Only recent snapshot for project tag")
@click.option('--all', 'list_all', default=False, is_flag=True, help="All snapshots for project tag")
def list_snapshots(project, list_all):

    """List all snapshots"""

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(','.join((
                s.id,
                v.id,
                i.id,
                s.state,
                s.progress,
                s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all:
                    break
    return

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None, help="Only volumes for project tag")
def list_volumes(project):
    """List all volumes"""
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(','.join((
            v.id,
            i.id,
            v.state,
            str(v.size)+"GiB",
            v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return

@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('list')
@click.option('--project', default=None, help="Only instances for project tag")
def list_instances(project):
    '''List EC2 instance'''

    instances = filter_instances(project)

    for i in instances:
        tags = {t['Key']:t['Value'] for t in i.tags or []}
        print(','.join((
        i.id,
        i.instance_type,
        i.placement['AvailabilityZone'],
        i.state['Name'],
        i.public_dns_name,
        tags.get('Name','<no name>')
        )))
    return

@instances.command('stop')
@click.option('--project', default=None, help="Stop instances for project tag")
def stop_instances(project):
    """Stop instances"""

    instances = filter_instances(project)

    for i in instances:
        print('Stopping {0}...'.format(i.id))
        try:
            i.stop()
        except:
            print("Could not stop {0}. ".format(i.id))
    return

@instances.command('start')
@click.option('--project', default=None, help="Start instances for project tag")
def start_instances(project):
    """Start instances"""

    instances = filter_instances(project)

    for i in instances:
        print('Starting {0}...'.format(i.id))
        try:
            i.start()
        except:
            print("Could not start {0}. ".format(i.id))
    return

@instances.command('snapshot')
@click.option('--project', default=None, help="Start instances for project tag")
def create_snapshot(project):
    """Start instances"""

    instances = filter_instances(project)

    for i in instances:
        i.stop()
        print("Stopping {0}...".format(i.id))
        i.wait_until_stopped()
        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("Skipping")
                continue
            print("Creating snapshot of {0}...".format(v.id))
            v.create_snapshot(Description="By snapagain")
        i.start()
        i.wait_until_running()
        print("Job's done!!")
    return

if __name__ == '__main__':
    cli()
