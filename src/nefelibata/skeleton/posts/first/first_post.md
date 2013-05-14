From nobody Tue May 14 10:41:10 2013
subject: This is your first post
publish-to: 
keywords: python, blog
date: Tue, 14 May 2013 10:40:28 -0700
summary: Just a simple summary of the Markdown syntax.

## Welcome ##

This is your first post. It should be written using Markdown.

Here's a quick summary of Markdown:

Paragraphs are separated by a blank line.

2nd paragraph. *Italic*, **bold**, `monospace`. Itemized lists
look like:

  * this one
  * that one
  * the other one

Note that --- not considering the asterisk --- the actual text
content starts at 4-columns in.

> Block quotes are
> written like so.
>
> They can span multiple paragraphs,
> if you like.

Use 3 dashes for an em-dash. Use 2 dashes for ranges (ex. "it's all in
chapters 12--14"). Three dots ... will be converted to an ellipsis.

Here's a numbered list:

 1. first item
 2. second item
 3. third item

Note again how the actual text starts at 4 columns in (4 characters
from the left side). Here's a Python code sample:

    #!python
    class DatasetType(StructureType):                                               
        def __setitem__(self, key, item):                                           
            if key != item.name:                                                    
                raise KeyError('Key "%s" is different from variable name "%s"!' %   
                    (key, item.name))                                               
            StructureType.__setitem__(self, key, item)                              
                                                                                    
            # The dataset name does not goes into the children ids.                 
            item.id = item.name                                                     
                                                                                    
        def _set_id(self, id):                                                      
            """                                                                     
            The method must be implemented so that the dataset name is not included 
            in the children ids.                                                    
                                                                                    
            """                                                                     
            self._id = id                                                           
                                                                                    
            for child in self.children():                                           
                child.id = child.name

As you probably guessed, indented 4 spaces. 
