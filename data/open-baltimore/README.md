# clean data

- clean 911
    - extract coordinates from column-location, drop rows w/o coordinates
    - parse date from callDatetime
    - map description to categories, drop "undefined" category
    - sort data by date
    - split dev(<2017-01-01)/test(>=2017-01-01) set  