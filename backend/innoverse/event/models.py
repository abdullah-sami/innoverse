from django.db import models



class Segment(models.Model):
    segment_name = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)

    def __str__(self):
        return f"{self.segment_name} ({self.code})"




class Gift(models.Model):
    gift_name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.gift_name




class Competition(models.Model):
    competition = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)


    def __str__(self):
        return f"{self.competition} ({self.code})"



class TeamCompetition(models.Model):
    competition = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)


    def __str__(self):
        return f"{self.competition} ({self.code})"
    



class Coupons(models.Model):
    coupon_code = models.CharField(max_length=50, unique=True, db_index=True, null=True, blank=True)
    discount = models.FloatField(default=10.0, db_index=True, null=True, blank=True)
    coupon_number = models.IntegerField(default=1000, db_index=True, null=True, blank=True)
    def __str__(self):
        return f"{self.coupon_code} - {self.discount}% - ({self.coupon_number} left)"