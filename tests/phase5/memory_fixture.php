<?php
declare(strict_types=1);
$mode=$argv[1]??'bounded';$rows=$mode==='unbounded'?20000:25;$data=[];
for($i=0;$i<$rows;$i++){
    $data[]=['id'=>$i,'title'=>str_repeat('T',120),'location_text'=>str_repeat('L',120),'description'=>str_repeat('D',500),'customer_name'=>'Customer '.$i,'category_name'=>'Category','service_name'=>'Service','status'=>'pending','created_at'=>'2026-09-24 12:00:00'];
}
$checksum=0;foreach($data as $row)$checksum+=strlen($row['title'])+strlen($row['description']);
echo json_encode(['mode'=>$mode,'rows'=>$rows,'peak_bytes'=>memory_get_peak_usage(true),'end_bytes'=>memory_get_usage(true),'checksum'=>$checksum],JSON_UNESCAPED_SLASHES).PHP_EOL;
