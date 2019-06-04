# This file is covered by the BSD license. See LICENSE in the root directory.
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

from . import models


@receiver(m2m_changed, sender=models.Dataset.linked_to.through)
def interconnect_all_links(sender, **kwargs):
    """Make linking of data sets transitive.

    If A is linked to B and B is linked to C then A and C should also
    be linked.

    """
    if kwargs['action'] == 'post_add' and kwargs['pk_set']:
        target_pk = list(kwargs['pk_set'])[0]
        direct_datasets = kwargs['instance'].linked_to.all()
        indirect_datasets = models.Dataset.objects.filter(
            linked_to__pk=target_pk)
        all_datasets = list(set(direct_datasets | indirect_datasets))
        for i in range(len(all_datasets)):
            dataset_i = all_datasets[i]
            for j in range(i+1, len(all_datasets)):
                dataset_j = all_datasets[j]
                if dataset_j not in dataset_i.linked_to.all():
                    dataset_i.linked_to.add(dataset_j)
