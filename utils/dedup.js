
var duplicates = [];

db.runCommand(
  {aggregate: "message_log",
    pipeline: [
      { $group: { _id: "$message_id", dups: { "$addToSet": "$_id" }, count: { "$sum": 1 } }},
      { $match: { count: { "$gt": 1 }}}
    ],
    allowDiskUse: true }
).result
.forEach(function(doc) {
    doc.dups.shift();
    doc.dups.forEach(function(dupId){ duplicates.push(dupId); })
});

db.message_log.remove({_id:{$in:duplicates}});