from __future__ import absolute_import, division, print_function
import sys
import pandas as pd
from pandasdmx import Request
from larray.core import Axis, df_aslarray

# ESTAT = Eurostat agency
estat = Request('ESTAT')


def get_eurostat_sdmx_variable(var_id, key=None):
    """
    get SDMX variable. Return its title, associated codelists and data.

    Parameters
    ----------
    var_id: str 
        the id of the variable to be requested. It is used for URL construction. 
    key: str or dict, optional
        select columns from a dataset by specifying dimension values.
        If 'key' is of type 'dict', it must map dimension names to allowed dimension values. 
        Two or more values can be separated by '+' as in the str form. 
        The DSD will be downloaded and the items are validated against it before downloading the dataset.

    Returns
    -------
    title: str
        title
    codelist: pandas.DataFrame
        codelists.
    arr: LArray
        data. 

    Examples
    --------
    >>> var_id = 'ilc_peps01'
    >>> key = {'GEO': 'BE+EU28', 'UNIT': 'PC_POP', 'AGE': 'TOTAL+Y18-64+Y_GE65+Y_LT18'}
    >>> title, codelist, data = get_eurostat_sdmx_variable(var_id, key)

    >>> # Show title
    >>> title
    'People at risk of poverty or social exclusion by age and sex'

    >>> # Show some code lists
    >>> codelist.ix[['SEX', 'UNIT']]
                  dim_or_attr                                           name
    SEX  SEX                D                                            SEX
         F                  D                                        Females
         M                  D                                          Males
         T                  D                                          Total
    UNIT UNIT               D                                           UNIT
         PC_POP             D                 Percentage of total population
         THS_CD08           D  Cumulative difference from 2008, in thousands
         THS_PER            D                               Thousand persons

    >>> # Explore the data set. 
    >>> # Show dimension names
    >>> data.columns.names
    FrozenList(['UNIT', 'AGE', 'SEX', 'GEO', 'FREQ'])
    >>> # Show dimension values
    >>> data.columns.levels
    FrozenList([['PC_POP'], ['TOTAL', 'Y18-64', 'Y_GE65', 'Y_LT18'], ['F', 'M', 'T'], ['BE', 'EU28'], ['A']])
    >>> # Show subset of dataset
    >>> data['PC_POP', 'TOTAL'].head(10)
    SEX             F           M           T      
    GEO            BE  EU28    BE  EU28    BE  EU28
    FREQ            A     A     A     A     A     A
    TIME_PERIOD                                    
    2016          NaN   NaN   NaN   NaN   NaN   NaN
    2015         22.2  24.4  20.0  23.0  21.1  23.7
    2014         21.5  25.2  20.9  23.6  21.2  24.4
    2013         21.2  25.5  20.4  23.7  20.8  24.6
    2012         22.3  25.7  20.9  23.7  21.6  24.7
    2011         21.5  25.3  20.4  23.1  21.0  24.3
    2010         21.7  24.8  20.0  22.6  20.8  23.7
    2009         21.8   NaN  18.5   NaN  20.2   NaN
    2008         22.4   NaN  19.1   NaN  20.8   NaN
    2007         23.1   NaN  19.9   NaN  21.6   NaN
    """
    if key is None:
        key = {}
    dataflow = estat.get('dataflow', var_id)
    title = dataflow.msg.dataflow[var_id].name['en']
    metadata = estat.datastructure("DSD_{}".format(var_id)).write()
    data_resp = estat.get(resource_type='data', resource_id=var_id, key=key)
    data = data_resp.msg.data
    df = data_resp.write(s for s in data.series)
    arr = df_aslarray(df.T, sort_columns=True)
    return title, metadata.codelist, arr


def describe_eurostat_data(arr, metadata):
    """
    
    :param arr: 
    :param metadata: 
    :return: 
    """
    def gettext(md, name, labels):
        cl = 'CL_{}'.format(name)
        if cl in md['name']:
            md_i = md['name'][cl]
            return ["{}: {}".format(l, md_i[l]) for l in labels if l in md_i]
        elif name in md['name']:
            md_i = md['name'][name]
            return ["{}: {}".format(l, md_i[l]) for l in labels if l in md_i]
        else:
            return labels

    en_axes = [Axis(name, gettext(metadata, name, axis.labels))
               for name, axis in zip(arr.axes.display_names, arr.axes._list)]
    en_arr = arr.with_axes(en_axes)
    return en_arr


def get_eurostat_sdmx(var_id, metadata=False, key=None):
    if key is None:
        title, df_metadata, data = get_eurostat_sdmx_variable(var_id)
    else:
        title, df_metadata, data = get_eurostat_sdmx_variable(var_id, key)

    if metadata:
        return describe_eurostat_data(data, df_metadata)
    else:
        return data
