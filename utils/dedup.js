/**
 * Created by Austin on 5/26/2017.
 */
var duplicates = [];

db.runCommand(
  {aggregate: "message_log",
    pipeline: [
      { $group: { _id: { DUPEFIELD: "$DUPEFIELD"}, dups: { "$addToSet": "$_id" }, count: { "$sum": 1 } }},
      { $match: { count: { "$gt": 1 }}}
    ],
    allowDiskUse: true }
)
.result
.forEach(function(doc) {
    doc.dups.shift();
    doc.dups.forEach(function(dupId){ duplicates.push(dupId); })
});
printjson(duplicates); //optional print the list of duplicates to be removed

db.message_log.remove({_id:{$in:duplicates}});